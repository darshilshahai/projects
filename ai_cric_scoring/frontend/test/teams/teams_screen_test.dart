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
  testWidgets('empty teams state offers create', (tester) async {
    await pumpManagementApp(tester);
    await _go(tester, AppRoutes.teams);

    expect(find.text('No teams yet'), findsOneWidget);
    expect(
      find.text('Create your first team and start building the squad.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('empty-create-team')), findsOneWidget);
  });

  testWidgets('team list renders owned teams', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(
        teams: [
          sampleTeam(playerCount: 12),
          sampleTeam(
            id: 'team-2',
            name: 'Office XI',
            shortName: 'OXI',
            playerCount: 9,
          ),
        ],
      ),
    );
    await _go(tester, AppRoutes.teams);

    expect(find.text('WEEKEND WARRIORS'), findsOneWidget);
    expect(find.text('OFFICE XI'), findsOneWidget);
    expect(find.text('12 PLAYERS'), findsOneWidget);
    expect(find.text('9 PLAYERS'), findsOneWidget);
  });

  testWidgets('create team validates empty name', (tester) async {
    await pumpManagementApp(tester);
    await _go(tester, AppRoutes.teamNew);

    await tester.tap(find.byKey(const Key('submit-team')));
    await tester.pump();

    expect(find.text('Team name is required.'), findsOneWidget);
  });

  testWidgets('successful create shows team detail', (tester) async {
    final teams = FakeTeamRepository();
    await pumpManagementApp(tester, teams: teams);
    await _go(tester, AppRoutes.teamNew);

    await tester.enterText(
      find.byKey(const Key('team-name-field')),
      'Weekend Warriors',
    );
    await tester.enterText(
      find.byKey(const Key('team-short-name-field')),
      'WW',
    );
    await tester.tap(find.byKey(const Key('submit-team')));
    await tester.pumpAndSettle();

    expect(find.text('WEEKEND WARRIORS'), findsWidgets);
    expect(find.byKey(const Key('manage-roster')), findsOneWidget);
    expect(teams.teams, hasLength(1));
  });

  testWidgets('duplicate team name shows friendly error', (tester) async {
    final teams = FakeTeamRepository(teams: [sampleTeam()]);
    await pumpManagementApp(tester, teams: teams);
    await _go(tester, AppRoutes.teamNew);

    await tester.enterText(
      find.byKey(const Key('team-name-field')),
      'Weekend Warriors',
    );
    await tester.tap(find.byKey(const Key('submit-team')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('team-form-error')), findsOneWidget);
    expect(
      find.text('You already have a team with this name.'),
      findsOneWidget,
    );
  });

  testWidgets('team detail shows roster action', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(teams: [sampleTeam(playerCount: 2)]),
    );
    await _go(tester, AppRoutes.team('team-1'));

    expect(find.text('WEEKEND WARRIORS'), findsWidgets);
    expect(find.text('ACTIVE'), findsWidgets);
    expect(find.byKey(const Key('manage-roster')), findsOneWidget);
    expect(find.byKey(const Key('edit-team')), findsOneWidget);
  });

  testWidgets('edit team updates name', (tester) async {
    final teams = FakeTeamRepository(teams: [sampleTeam()]);
    await pumpManagementApp(tester, teams: teams);
    await _go(tester, AppRoutes.teamEdit('team-1'));

    await tester.enterText(
      find.byKey(const Key('team-name-field')),
      'Night Warriors',
    );
    await tester.tap(find.byKey(const Key('submit-team')));
    await tester.pumpAndSettle();

    expect(teams.teams.single.name, 'Night Warriors');
  });

  testWidgets('manage roster navigates to roster screen', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(teams: [sampleTeam()]),
    );
    await _go(tester, AppRoutes.team('team-1'));

    await tester.tap(find.byKey(const Key('manage-roster')));
    await tester.pumpAndSettle();

    expect(find.text('Empty roster'), findsOneWidget);
    expect(find.byKey(const Key('add-player-to-roster')), findsOneWidget);
  });
}
