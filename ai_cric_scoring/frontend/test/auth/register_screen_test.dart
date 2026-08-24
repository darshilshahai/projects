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

  Future<void> pumpRegister(WidgetTester tester) {
    return pumpCricketApp(
      tester,
      overrides: [
        authRepositoryProvider.overrideWithValue(repository),
        authControllerProvider.overrideWith(UnauthenticatedAuthController.new),
      ],
    );
  }

  Future<void> openRegister(WidgetTester tester) async {
    await pumpRegister(tester);
    await tester.tap(find.text('CREATE ACCOUNT'));
    await tester.pumpAndSettle();
  }

  testWidgets('register form renders', (tester) async {
    await openRegister(tester);

    expect(find.text('CREATE'), findsOneWidget);
    expect(find.text('ACCOUNT.'), findsOneWidget);
    expect(find.text('DISPLAY NAME'), findsOneWidget);
    expect(find.text('EMAIL'), findsOneWidget);
    expect(find.text('PASSWORD'), findsOneWidget);
    expect(find.text('CONFIRM PASSWORD'), findsOneWidget);
    expect(find.text('CREATE ACCOUNT'), findsWidgets);
  });

  testWidgets('register validates email and password', (tester) async {
    await openRegister(tester);

    await tester.enterText(find.byKey(const Key('register-email')), 'bad');
    await tester.enterText(find.byKey(const Key('register-password')), 'short');
    await tester.enterText(find.byKey(const Key('register-confirm')), 'short');
    await tester.ensureVisible(find.byKey(const Key('register-submit')));
    await tester.tap(find.byKey(const Key('register-submit')));
    await tester.pump();

    expect(find.text('Enter a valid email.'), findsOneWidget);
    expect(
      find.text('Password must be at least 8 characters.'),
      findsOneWidget,
    );
  });

  testWidgets('register rejects password confirmation mismatch', (
    tester,
  ) async {
    await openRegister(tester);

    await tester.enterText(
      find.byKey(const Key('register-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('register-password')),
      'strong-password',
    );
    await tester.enterText(
      find.byKey(const Key('register-confirm')),
      'other-password',
    );
    await tester.ensureVisible(find.byKey(const Key('register-submit')));
    await tester.tap(find.byKey(const Key('register-submit')));
    await tester.pump();

    expect(find.text('Passwords do not match.'), findsOneWidget);
  });

  testWidgets('successful register reaches home', (tester) async {
    when(
      () => repository.register(
        email: any(named: 'email'),
        password: any(named: 'password'),
        displayName: any(named: 'displayName'),
      ),
    ).thenAnswer((_) async => testAuthenticatedUser);

    await openRegister(tester);
    await tester.enterText(
      find.byKey(const Key('register-display-name')),
      'Darshil',
    );
    await tester.enterText(
      find.byKey(const Key('register-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('register-password')),
      'strong-password',
    );
    await tester.enterText(
      find.byKey(const Key('register-confirm')),
      'strong-password',
    );
    await tester.ensureVisible(find.byKey(const Key('register-submit')));
    await tester.tap(find.byKey(const Key('register-submit')));
    await tester.pumpAndSettle();

    expect(find.text('START NEW MATCH'), findsOneWidget);
    verify(
      () => repository.register(
        email: 'user@example.com',
        password: 'strong-password',
        displayName: 'Darshil',
      ),
    ).called(1);
  });

  testWidgets('duplicate email is mapped for the user', (tester) async {
    when(
      () => repository.register(
        email: any(named: 'email'),
        password: any(named: 'password'),
        displayName: any(named: 'displayName'),
      ),
    ).thenThrow(
      const ApiException(
        'An account with this email already exists.',
        statusCode: 409,
        code: 'EMAIL_ALREADY_REGISTERED',
      ),
    );

    await openRegister(tester);
    await tester.enterText(
      find.byKey(const Key('register-email')),
      'user@example.com',
    );
    await tester.enterText(
      find.byKey(const Key('register-password')),
      'strong-password',
    );
    await tester.enterText(
      find.byKey(const Key('register-confirm')),
      'strong-password',
    );
    await tester.ensureVisible(find.byKey(const Key('register-submit')));
    await tester.tap(find.byKey(const Key('register-submit')));
    await tester.pump();

    expect(
      find.text('An account with this email already exists.'),
      findsOneWidget,
    );
    expect(find.textContaining('DioException'), findsNothing);
  });
}
