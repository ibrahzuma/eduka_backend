import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/auth_repository.dart';

final authRepositoryProvider = Provider((ref) => AuthRepository());

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(authRepositoryProvider));
});

enum AuthStatus { authenticated, unauthenticated, loading }

class AuthState {
  final AuthStatus status;
  final String? error;

  AuthState({required this.status, this.error});
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository)
    : super(AuthState(status: AuthStatus.loading)) {
    checkStatus();
  }

  Future<void> checkStatus() async {
    final isLoggedIn = await _repository.isLoggedIn();
    state = AuthState(
      status: isLoggedIn
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated,
    );
  }

  Future<void> login(String username, String password) async {
    state = AuthState(status: AuthStatus.loading);
    final success = await _repository.login(username, password);
    if (success) {
      state = AuthState(status: AuthStatus.authenticated);
    } else {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        error: 'Login Failed',
      );
    }
  }

  Future<void> logout() async {
    await _repository.logout();
    state = AuthState(status: AuthStatus.unauthenticated);
  }
}
