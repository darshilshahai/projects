import 'package:ai_cric_scoring/app/app.dart';
import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/auth/data/repositories/auth_repository.dart';
import 'package:ai_cric_scoring/features/auth/presentation/providers/auth_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import '../helpers/auth_controllers.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  late MockAuthRepository repository;

  setUp(() {
    repository = MockAuthRepository();
    when(repository.clearLocal).thenAnswer((_) async {});
  });

  Future<void> pumpRealAuth(WidgetTester tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
        child: const CricketIntelligenceApp(),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('valid stored session restores to home', (tester) async {
    when(
      repository.restoreSession,
    ).thenAnswer((_) async => testAuthenticatedUser);
    await pumpRealAuth(tester);
    expect(find.text('START NEW MATCH'), findsOneWidget);
  });

  testWidgets('rejected restore shows login', (tester) async {
    when(
      repository.restoreSession,
    ).thenThrow(const ApiException('Not signed in.', statusCode: 401));
    await pumpRealAuth(tester);
    expect(find.text('WELCOME'), findsOneWidget);
    verify(repository.clearLocal).called(1);
  });

  testWidgets('network failure during restore does not show login', (
    tester,
  ) async {
    when(
      repository.restoreSession,
    ).thenThrow(const ApiException('Unable to reach the backend.'));
    await pumpRealAuth(tester);
    expect(find.byKey(const Key('splash-screen')), findsOneWidget);
    expect(find.text('RETRY'), findsOneWidget);
    expect(find.text('WELCOME'), findsNothing);
    verifyNever(repository.clearLocal);
  });
}
