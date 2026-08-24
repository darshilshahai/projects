import 'package:ai_cric_scoring/features/auth/data/models/auth_tokens.dart';
import 'package:ai_cric_scoring/features/auth/presentation/controllers/auth_state.dart';
import 'package:ai_cric_scoring/features/auth/presentation/providers/auth_providers.dart';

const testAuthenticatedUser = AuthenticatedUser(
  id: 'test-user-id',
  email: 'tester@example.com',
  displayName: 'Tester',
  isActive: true,
);

class AuthenticatedAuthController extends AuthController {
  @override
  AuthState build() => const AuthAuthenticated(testAuthenticatedUser);
}

class UnauthenticatedAuthController extends AuthController {
  @override
  AuthState build() => const AuthUnauthenticated();
}

class InitializingAuthController extends AuthController {
  @override
  AuthState build() => const AuthInitializing();
}

class FailureAuthController extends AuthController {
  FailureAuthController(this.message);

  final String message;

  @override
  AuthState build() => AuthFailure(message);
}
