import 'package:ai_cric_scoring/core/cricket/player_attributes.dart';
import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/features/home/presentation/screens/home_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_management_repos.dart';
import '../helpers/pump_app.dart';

Future<void> _go(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(HomeScreen));
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('empty players state offers create', (tester) async {
    await pumpManagementApp(tester);
    await _go(tester, AppRoutes.players);

    expect(find.text('No players yet'), findsOneWidget);
    expect(
      find.text('Build your player pool once, then add them to any team.'),
      findsOneWidget,
    );
  });

  testWidgets('player list renders names and roles', (tester) async {
    await pumpManagementApp(
      tester,
      players: FakePlayerRepository(
        players: [
          samplePlayer(),
          samplePlayer(
            id: 'player-2',
            name: 'Arjun Mehta',
            role: PlayerRole.allRounder,
          ),
        ],
      ),
    );
    await _go(tester, AppRoutes.players);

    expect(find.text('RAHUL SHAH'), findsOneWidget);
    expect(find.text('ARJUN MEHTA'), findsOneWidget);
    expect(find.text('BATTER'), findsWidgets);
    expect(find.text('ALL-ROUNDER'), findsOneWidget);
  });

  testWidgets('player search and role filter', (tester) async {
    await pumpManagementApp(
      tester,
      players: FakePlayerRepository(
        players: [
          samplePlayer(),
          samplePlayer(
            id: 'player-2',
            name: 'Arjun Mehta',
            role: PlayerRole.bowler,
          ),
        ],
      ),
    );
    await _go(tester, AppRoutes.players);

    await tester.enterText(find.byKey(const Key('player-search')), 'Arjun');
    await tester.pumpAndSettle();
    expect(find.text('ARJUN MEHTA'), findsOneWidget);
    expect(find.text('RAHUL SHAH'), findsNothing);

    await tester.enterText(find.byKey(const Key('player-search')), '');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('player-filter-BOWLER')));
    await tester.pumpAndSettle();
    expect(find.text('ARJUN MEHTA'), findsOneWidget);
    expect(find.text('RAHUL SHAH'), findsNothing);
  });

  testWidgets('create player validates empty name', (tester) async {
    await pumpManagementApp(tester);
    await _go(tester, AppRoutes.playerNew);

    await tester.ensureVisible(find.byKey(const Key('submit-player')));
    await tester.tap(find.byKey(const Key('submit-player')));
    await tester.pump();

    expect(find.text('Player name is required.'), findsOneWidget);
  });

  testWidgets('enum selector updates role label', (tester) async {
    await pumpManagementApp(tester);
    await _go(tester, AppRoutes.playerNew);

    expect(find.text('Batter'), findsOneWidget);
    await tester.tap(find.byKey(const Key('player-role-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('All-rounder'));
    await tester.pumpAndSettle();
    expect(find.text('All-rounder'), findsOneWidget);
  });

  testWidgets('successful create shows player detail', (tester) async {
    final players = FakePlayerRepository();
    await pumpManagementApp(tester, players: players);
    await _go(tester, AppRoutes.playerNew);

    await tester.enterText(
      find.byKey(const Key('player-name-field')),
      'Rahul Shah',
    );
    await tester.ensureVisible(find.byKey(const Key('submit-player')));
    await tester.tap(find.byKey(const Key('submit-player')));
    await tester.pumpAndSettle();

    expect(find.text('RAHUL SHAH'), findsWidgets);
    expect(find.text('Batter'), findsOneWidget);
    expect(find.text('Right-handed'), findsOneWidget);
    expect(players.players, hasLength(1));
  });

  testWidgets('edit player updates metadata', (tester) async {
    final players = FakePlayerRepository(players: [samplePlayer()]);
    await pumpManagementApp(tester, players: players);
    await _go(tester, AppRoutes.playerEdit('player-1'));

    await tester.enterText(
      find.byKey(const Key('player-name-field')),
      'Rahul Patel',
    );
    await tester.ensureVisible(find.byKey(const Key('submit-player')));
    await tester.tap(find.byKey(const Key('submit-player')));
    await tester.pumpAndSettle();

    expect(players.players.single.name, 'Rahul Patel');
  });

  testWidgets('inactive player shows status on detail', (tester) async {
    await pumpManagementApp(
      tester,
      players: FakePlayerRepository(players: [samplePlayer(isActive: false)]),
    );
    await _go(tester, AppRoutes.player('player-1'));

    expect(find.text('INACTIVE'), findsWidgets);
    expect(find.byKey(const Key('edit-player')), findsOneWidget);
  });
}
