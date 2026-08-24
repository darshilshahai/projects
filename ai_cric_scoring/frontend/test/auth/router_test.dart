import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/features/auth/presentation/providers/auth_providers.dart';
import 'package:ai_cric_scoring/features/home/presentation/screens/home_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/auth_controllers.dart';
import '../helpers/fake_management_repos.dart';
import '../helpers/pump_app.dart';

void main() {
  testWidgets('initializing shows splash', (tester) async {
    await pumpCricketApp(
      tester,
      overrides: [
        authControllerProvider.overrideWith(InitializingAuthController.new),
      ],
    );

    expect(find.byKey(const Key('splash-screen')), findsOneWidget);
    expect(find.text('Session.'), findsOneWidget);
    expect(find.text('WELCOME'), findsNothing);
    expect(find.text('START NEW MATCH'), findsNothing);
  });

  testWidgets('unauthenticated shows login', (tester) async {
    await pumpCricketApp(
      tester,
      overrides: [
        authControllerProvider.overrideWith(UnauthenticatedAuthController.new),
      ],
    );

    expect(find.text('WELCOME'), findsOneWidget);
    expect(find.text('START NEW MATCH'), findsNothing);
  });

  testWidgets('authenticated shows home', (tester) async {
    await pumpCricketApp(tester);

    expect(find.text('START NEW MATCH'), findsOneWidget);
    expect(find.text('WELCOME'), findsNothing);
  });

  testWidgets('authenticated login route redirects to home', (tester) async {
    await pumpCricketApp(tester);

    final context = tester.element(find.byType(HomeScreen));
    GoRouter.of(context).go(AppRoutes.login);
    await tester.pumpAndSettle();

    expect(find.text('START NEW MATCH'), findsOneWidget);
    expect(find.text('WELCOME'), findsNothing);
  });

  testWidgets('unauthenticated match routes redirect to login', (tester) async {
    await pumpCricketApp(
      tester,
      overrides: [
        authControllerProvider.overrideWith(UnauthenticatedAuthController.new),
      ],
    );

    final context = tester.element(find.text('WELCOME'));
    for (final location in [
      AppRoutes.matchNew,
      '/matches/match-1',
      '/matches/match-1/setup',
      '/matches/match-1/scorecard',
      '/matches/match-1/analysis',
      '/matches/match-1/chat',
      '/stats/players/player-1',
      AppRoutes.statsAsk,
    ]) {
      GoRouter.of(context).go(location);
      await tester.pumpAndSettle();
      expect(find.text('WELCOME'), findsOneWidget, reason: location);
      expect(find.text('SELECT FORMAT'), findsNothing);
    }
  });

  testWidgets('authenticated management routes stay protected', (tester) async {
    final teams = FakeTeamRepository(teams: [sampleTeam()]);
    final players = FakePlayerRepository(players: [samplePlayer()]);
    await pumpManagementApp(tester, teams: teams, players: players);

    final router = GoRouter.of(tester.element(find.byType(HomeScreen)));
    const locations = [
      AppRoutes.teams,
      AppRoutes.teamNew,
      '/teams/team-1',
      '/teams/team-1/edit',
      '/teams/team-1/roster',
      AppRoutes.players,
      AppRoutes.playerNew,
      '/players/player-1',
      AppRoutes.matches,
      AppRoutes.matchNew,
      '/matches/match-1',
      '/matches/match-1/setup',
      '/matches/match-1/scorecard',
      '/matches/match-1/analysis',
      '/matches/match-1/chat',
      '/stats/players/player-1',
      '/stats/teams/team-1',
      AppRoutes.statsComparePlayers,
      AppRoutes.statsCompareTeams,
      AppRoutes.statsAsk,
    ];
    for (final location in locations) {
      router.go(location);
      await tester.pumpAndSettle();
      expect(find.text('WELCOME'), findsNothing, reason: location);
      expect(find.byKey(const Key('splash-screen')), findsNothing);
    }
  });
}
