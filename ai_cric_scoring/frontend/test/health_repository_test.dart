import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/core/network/api_client.dart';
import 'package:ai_cric_scoring/core/network/api_endpoints.dart';
import 'package:ai_cric_scoring/features/home/data/health_repository.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  test('parses a healthy API response', () async {
    final client = MockApiClient();
    when(() => client.getJson(ApiEndpoints.health)).thenAnswer(
      (_) async => {
        'status': 'ok',
        'service': 'cricket-intelligence-api',
        'environment': 'development',
        'database': 'connected',
      },
    );

    final repository = HealthRepository(apiClient: client);
    final result = await repository.checkHealth();

    expect(result.status, 'ok');
    expect(result.database, 'connected');
  });

  test('propagates API failures', () async {
    final client = MockApiClient();
    when(
      () => client.getJson(ApiEndpoints.health),
    ).thenThrow(const ApiException('Unable to reach the backend.'));

    final repository = HealthRepository(apiClient: client);

    expect(
      repository.checkHealth(),
      throwsA(
        isA<ApiException>().having(
          (error) => error.message,
          'message',
          'Unable to reach the backend.',
        ),
      ),
    );
  });
}
