import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:ai_cric_scoring/core/network/api_client.dart';
import 'package:ai_cric_scoring/core/network/api_endpoints.dart';
import 'package:ai_cric_scoring/core/network/auth_interceptor.dart';
import 'package:ai_cric_scoring/features/auth/data/models/auth_tokens.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import '../helpers/memory_auth_local_data_source.dart';

class _ScriptedAdapter implements HttpClientAdapter {
  _ScriptedAdapter(this._handler);

  final Future<ResponseBody> Function(RequestOptions options) _handler;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) {
    return _handler(options);
  }
}

ResponseBody _json(Object body, int status) {
  return ResponseBody.fromString(
    jsonEncode(body),
    status,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );
}

void main() {
  late MemoryAuthLocalDataSource local;
  late Dio dio;
  late ApiClient client;
  late List<String> authorizationHeaders;
  late int refreshCount;
  late int meCount;

  setUp(() {
    local = MemoryAuthLocalDataSource(
      accessToken: 'expired-access',
      refreshToken: 'refresh-1',
    );
    authorizationHeaders = [];
    refreshCount = 0;
    meCount = 0;
    dio = Dio(
      BaseOptions(
        baseUrl: 'http://example.test',
        headers: const {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );
    client = ApiClient.fromDio(dio);
    dio.interceptors.add(
      AuthInterceptor(
        dio: dio,
        localDataSource: local,
        refreshTokens: (refreshToken) async {
          final json = await client.postJson(
            ApiEndpoints.refresh,
            data: {'refresh_token': refreshToken},
            skipAuth: true,
          );
          return AuthTokens.fromJson(
            Map<String, dynamic>.from(json['tokens'] as Map),
          );
        },
        onSessionInvalidated: () {},
      ),
    );
  });

  test('attaches Authorization header', () async {
    local.accessToken = 'access-live';
    dio.httpClientAdapter = _ScriptedAdapter((options) async {
      authorizationHeaders.add(
        options.headers['Authorization']?.toString() ?? '',
      );
      return _json({'id': '1', 'email': 'a@b.com', 'is_active': true}, 200);
    });

    await client.getJson(ApiEndpoints.me);

    expect(authorizationHeaders, ['Bearer access-live']);
  });

  test('expired access refreshes and retries the original request', () async {
    dio.httpClientAdapter = _ScriptedAdapter((options) async {
      if (options.path.endsWith('/auth/refresh')) {
        refreshCount += 1;
        return _json({
          'user': {'id': '1', 'email': 'a@b.com', 'is_active': true},
          'tokens': {
            'access_token': 'access-2',
            'refresh_token': 'refresh-2',
            'token_type': 'bearer',
          },
        }, 200);
      }
      meCount += 1;
      final auth = options.headers['Authorization']?.toString();
      if (auth == 'Bearer expired-access') {
        return _json({
          'error': {'code': 'TOKEN_EXPIRED', 'message': 'expired'},
        }, 401);
      }
      authorizationHeaders.add(auth ?? '');
      return _json({'id': '1', 'email': 'a@b.com', 'is_active': true}, 200);
    });

    final body = await client.getJson(ApiEndpoints.me);

    expect(refreshCount, 1);
    expect(meCount, 2);
    expect(body['email'], 'a@b.com');
    expect(local.accessToken, 'access-2');
    expect(local.refreshToken, 'refresh-2');
    expect(authorizationHeaders, ['Bearer access-2']);
  });

  test('concurrent 401s share a single refresh', () async {
    final refreshStarted = Completer<void>();
    final releaseRefresh = Completer<void>();

    dio.httpClientAdapter = _ScriptedAdapter((options) async {
      if (options.path.endsWith('/auth/refresh')) {
        refreshCount += 1;
        refreshStarted.complete();
        await releaseRefresh.future;
        return _json({
          'user': {'id': '1', 'email': 'a@b.com', 'is_active': true},
          'tokens': {
            'access_token': 'access-2',
            'refresh_token': 'refresh-2',
            'token_type': 'bearer',
          },
        }, 200);
      }
      final auth = options.headers['Authorization']?.toString();
      if (auth == 'Bearer expired-access') {
        return _json({
          'error': {'code': 'TOKEN_EXPIRED', 'message': 'expired'},
        }, 401);
      }
      return _json({'ok': true}, 200);
    });

    final requests = [
      client.getJson('/api/v1/protected-a'),
      client.getJson('/api/v1/protected-b'),
      client.getJson('/api/v1/protected-c'),
      client.getJson('/api/v1/protected-d'),
      client.getJson('/api/v1/protected-e'),
    ];

    await refreshStarted.future;
    expect(refreshCount, 1);
    releaseRefresh.complete();
    await Future.wait(requests);
    expect(refreshCount, 1);
  });
}
