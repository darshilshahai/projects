import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/auth/data/datasources/auth_remote_data_source.dart';
import 'package:ai_cric_scoring/features/auth/data/models/auth_tokens.dart';
import 'package:ai_cric_scoring/features/auth/data/repositories/auth_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import '../helpers/memory_auth_local_data_source.dart';

class MockRemote extends Mock implements AuthRemoteDataSource {}

void main() {
  const user = AuthenticatedUser(
    id: 'user-1',
    email: 'user@example.com',
    displayName: 'Darshil',
    isActive: true,
  );
  const tokens = AuthTokens(accessToken: 'access-2', refreshToken: 'refresh-2');
  const session = AuthSession(user: user, tokens: tokens);

  test('no refresh token restores as unauthenticated', () async {
    final local = MemoryAuthLocalDataSource();
    final remote = MockRemote();
    final repository = AuthRepository(remote: remote, local: local);

    expect(
      repository.restoreSession(),
      throwsA(isA<ApiException>().having((e) => e.statusCode, 'status', 401)),
    );
    verifyNever(() => remote.me());
  });

  test('valid stored session uses /me', () async {
    final local = MemoryAuthLocalDataSource(
      accessToken: 'access',
      refreshToken: 'refresh',
    );
    final remote = MockRemote();
    when(remote.me).thenAnswer((_) async => user);
    final repository = AuthRepository(remote: remote, local: local);

    expect(await repository.restoreSession(), user);
    verify(remote.me).called(1);
    verifyNever(() => remote.refresh(any()));
  });

  test('expired access with valid refresh rotates tokens', () async {
    final local = MemoryAuthLocalDataSource(
      accessToken: 'expired',
      refreshToken: 'refresh-1',
    );
    final remote = MockRemote();
    when(remote.me).thenThrow(
      const ApiException('The access token has expired.', statusCode: 401),
    );
    when(() => remote.refresh('refresh-1')).thenAnswer((_) async => session);
    final repository = AuthRepository(remote: remote, local: local);

    expect(await repository.restoreSession(), user);
    expect(local.accessToken, 'access-2');
    expect(local.refreshToken, 'refresh-2');
  });

  test('rejected refresh does not keep working credentials', () async {
    final local = MemoryAuthLocalDataSource(
      accessToken: 'expired',
      refreshToken: 'refresh-1',
    );
    final remote = MockRemote();
    when(remote.me).thenThrow(
      const ApiException('The access token has expired.', statusCode: 401),
    );
    when(() => remote.refresh('refresh-1')).thenThrow(
      const ApiException('This session is no longer valid.', statusCode: 401),
    );
    final repository = AuthRepository(remote: remote, local: local);

    await expectLater(
      repository.restoreSession(),
      throwsA(
        isA<ApiException>().having((e) => e.isUnauthorized, '401', isTrue),
      ),
    );
    expect(local.refreshToken, 'refresh-1');
  });

  test('network failure during refresh keeps stored credentials', () async {
    final local = MemoryAuthLocalDataSource(
      accessToken: 'expired',
      refreshToken: 'refresh-1',
    );
    final remote = MockRemote();
    when(remote.me).thenThrow(
      const ApiException('The access token has expired.', statusCode: 401),
    );
    when(
      () => remote.refresh('refresh-1'),
    ).thenThrow(const ApiException('Unable to reach the backend.'));
    final repository = AuthRepository(remote: remote, local: local);

    await expectLater(
      repository.restoreSession(),
      throwsA(
        isA<ApiException>().having(
          (e) => e.isNetworkFailure,
          'network',
          isTrue,
        ),
      ),
    );
    expect(local.refreshToken, 'refresh-1');
    expect(local.accessToken, 'expired');
  });
}
