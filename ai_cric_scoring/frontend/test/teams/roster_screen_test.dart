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
  testWidgets('empty roster state', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(teams: [sampleTeam()]),
    );
    await _go(tester, AppRoutes.teamRoster('team-1'));

    expect(find.text('Empty roster'), findsOneWidget);
    expect(find.byKey(const Key('add-player-to-roster')), findsOneWidget);
  });

  testWidgets('roster list shows members', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(
        teams: [sampleTeam(playerCount: 2)],
        roster: {
          'team-1': [
            sampleRosterMember(),
            sampleRosterMember(
              membershipId: 'membership-2',
              playerId: 'player-2',
              name: 'Arjun Mehta',
              role: PlayerRole.allRounder,
            ),
          ],
        },
      ),
    );
    await _go(tester, AppRoutes.teamRoster('team-1'));

    expect(find.text('RAHUL SHAH'), findsOneWidget);
    expect(find.text('ARJUN MEHTA'), findsOneWidget);
  });

  testWidgets('already-added player is excluded from add picker', (
    tester,
  ) async {
    final rahul = samplePlayer();
    final arjun = samplePlayer(
      id: 'player-2',
      name: 'Arjun Mehta',
      role: PlayerRole.bowler,
    );
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(
        teams: [sampleTeam(playerCount: 1)],
        roster: {
          'team-1': [sampleRosterMember()],
        },
        playerPool: [rahul, arjun],
      ),
      players: FakePlayerRepository(players: [rahul, arjun]),
    );
    await _go(tester, AppRoutes.teamRosterAdd('team-1'));

    expect(find.text('RAHUL SHAH'), findsNothing);
    expect(find.text('ARJUN MEHTA'), findsOneWidget);
  });

  testWidgets('add player to roster', (tester) async {
    final rahul = samplePlayer();
    final teams = FakeTeamRepository(
      teams: [sampleTeam()],
      playerPool: [rahul],
    );
    await pumpManagementApp(
      tester,
      teams: teams,
      players: FakePlayerRepository(players: [rahul]),
    );
    await _go(tester, AppRoutes.teamRosterAdd('team-1'));

    await tester.tap(find.byKey(const Key('add-roster-player-player-1')));
    await tester.pumpAndSettle();

    expect(teams.rosterByTeam['team-1'], hasLength(1));
    expect(teams.rosterByTeam['team-1']!.single.playerId, 'player-1');
  });

  testWidgets('remove player shows confirmation then removes', (tester) async {
    final teams = FakeTeamRepository(
      teams: [sampleTeam(playerCount: 1)],
      roster: {
        'team-1': [sampleRosterMember()],
      },
    );
    await pumpManagementApp(tester, teams: teams);
    await _go(tester, AppRoutes.teamRoster('team-1'));

    await tester.tap(find.byKey(const Key('remove-roster-player-1')));
    await tester.pumpAndSettle();
    expect(
      find.text('Remove Rahul Shah from Weekend Warriors?'),
      findsOneWidget,
    );
    expect(
      find.textContaining('The player will remain in your player pool.'),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const Key('confirm-accept')));
    await tester.pumpAndSettle();

    expect(teams.rosterByTeam['team-1']!.single.isActive, isFalse);
    expect(find.text('Empty roster'), findsOneWidget);
  });
}
