import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/auth/data/repositories/auth_repository.dart';
import 'package:ai_cric_scoring/features/auth/presentation/providers/auth_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import '../helpers/auth_controllers.dart';
import '../helpers/pump_app.dart';

class MockAuthRepository extends Mock implements AuthRepository {}

void main() {
  late MockAuthRepository repository;

  setUp(() {
    repository = MockAuthRepository();
  });

  Future<void> pumpLogin(WidgetTester tester) {
    return pumpCricketApp(
      tester,
      overrides: [
        authRepositoryProvider.overrideWithValue(repository),
        authControllerProvider.overrideWith(UnauthenticatedAuthController.new),
      ],
    );
  }

  testWidgets('login screen renders', (tester) async {
    await pumpLogin(tester);

    expect(find.text('WELCOME'), findsOneWidget);
    expect(find.text('BACK.'), findsOneWidget);
    expect(find.text('EMAIL'), findsOneWidget);
    expect(find.text('PASSWORD'), findsOneWidget);
    expect(find.text('SIGN IN'), findsOneWidget);
  });

  testWidgets('login validates empty fields', (tester) async {
    await pumpLogin(tester);

    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(find.text('Enter your email.'), findsOneWidget);
    expect(find.text('Enter your password.'), findsOneWidget);
  });

  testWidgets('login validates email format', (tester) async {
    await pumpLogin(tester);

    await tester.enterText(
      find.byKey(const Key('login-email')),
      'not-an-email',
    );
    await tester.enterText(find.byKey(const Key('login-password')), 'password');
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(find.text('Enter a valid email.'), findsOneWidget);
  });

  testWidgets('login shows loading state', (tester) async {
    when(
      () => repository.login(
        email: any(named: 'email'),
        password: any(named: 'password'),
      ),
    ).thenAnswer((_) async {
      await Future<void>.delayed(const Duration(milliseconds: 400));
      return testAuthenticatedUser;
    });

    await pumpLogin(tester);
    await tester.enterText(
      find.byKey(const Key('login-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('login-password')),
      'strong-password',
    );
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 400));
    await tester.pumpAndSettle();
  });

  testWidgets('successful login reaches home', (tester) async {
    when(
      () => repository.login(
        email: any(named: 'email'),
        password: any(named: 'password'),
      ),
    ).thenAnswer((_) async => testAuthenticatedUser);

    await pumpLogin(tester);
    await tester.enterText(
      find.byKey(const Key('login-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('login-password')),
      'strong-password',
    );
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pumpAndSettle();

    expect(find.text('START NEW MATCH'), findsOneWidget);
    verify(
      () => repository.login(
        email: 'user@example.com',
        password: 'strong-password',
      ),
    ).called(1);
  });

  testWidgets('invalid credentials are mapped for the user', (tester) async {
    when(
      () => repository.login(
        email: any(named: 'email'),
        password: any(named: 'password'),
      ),
    ).thenThrow(
      const ApiException(
        'Invalid email or password.',
        statusCode: 401,
        code: 'INVALID_CREDENTIALS',
      ),
    );

    await pumpLogin(tester);
    await tester.enterText(
      find.byKey(const Key('login-email')),
      'user@example.com',
    );
    await tester.enterText(find.byKey(const Key('login-password')), 'wrong');
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(find.text('Incorrect email or password.'), findsOneWidget);
    expect(find.textContaining('DioException'), findsNothing);
  });

  testWidgets('network failure is mapped for the user', (tester) async {
    when(
      () => repository.login(
        email: any(named: 'email'),
        password: any(named: 'password'),
      ),
    ).thenThrow(const ApiException('Unable to reach the backend.'));

    await pumpLogin(tester);
    await tester.enterText(
      find.byKey(const Key('login-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('login-password')),
      'strong-password',
    );
    await tester.tap(find.byKey(const Key('login-submit')));
    await tester.pump();

    expect(
      find.text('Unable to connect. Check your connection and try again.'),
      findsOneWidget,
    );
  });
}
