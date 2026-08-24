import 'package:ai_cric_scoring/core/cricket/player_attributes.dart';
import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/features/home/presentation/screens/home_screen.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/teams/data/models/roster_member.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_management_repos.dart';
import '../helpers/fake_match_repo.dart';
import '../helpers/pump_app.dart';

Future<void> _go(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(HomeScreen));
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

List<RosterMember> _roster(String prefix, int count) {
  return [
    for (var i = 1; i <= count; i++)
      sampleRosterMember(
        membershipId: '$prefix-m-$i',
        playerId: '$prefix-p-$i',
        name: '$prefix Player $i',
        role: i == 1 ? PlayerRole.batter : PlayerRole.bowler,
      ),
  ];
}

FakeTeamRepository _twoTeams({int rosterSize = 8}) {
  return FakeTeamRepository(
    teams: [
      sampleTeam(
        id: 'team-1',
        name: 'Weekend Warriors',
        playerCount: rosterSize,
      ),
      sampleTeam(
        id: 'team-2',
        name: 'Office XI',
        shortName: 'OXI',
        playerCount: rosterSize,
      ),
    ],
    roster: {
      'team-1': _roster('A', rosterSize),
      'team-2': _roster('B', rosterSize),
    },
  );
}

void main() {
  testWidgets('empty matches state offers create', (tester) async {
    await pumpManagementApp(tester);
    await tester.tap(find.byKey(const Key('nav-matches')));
    await tester.pumpAndSettle();

    expect(find.text('No matches yet'), findsOneWidget);
    expect(
      find.text(
        'Set up your first match, select the squads and prepare the scoring desk.',
      ),
      findsOneWidget,
    );
    expect(find.byKey(const Key('empty-create-match')), findsOneWidget);
  });

  testWidgets('match list renders draft and ready matches', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(
        matches: [
          sampleMatch(
            id: 'match-ready',
            status: MatchStatus.ready,
            teams: [
              sampleMatchTeam(
                id: 'mt-a',
                teamId: 'team-1',
                side: MatchSide.teamA,
                name: 'Weekend Warriors',
              ),
              sampleMatchTeam(
                id: 'mt-b',
                teamId: 'team-2',
                side: MatchSide.teamB,
                name: 'Office XI',
              ),
            ],
          ),
          sampleMatch(
            id: 'match-draft',
            status: MatchStatus.draft,
            teams: [
              sampleMatchTeam(
                id: 'mt-a2',
                teamId: 'team-3',
                side: MatchSide.teamA,
                name: 'Titans',
              ),
              sampleMatchTeam(
                id: 'mt-b2',
                teamId: 'team-4',
                side: MatchSide.teamB,
                name: 'Warriors',
              ),
            ],
          ),
        ],
      ),
    );
    await tester.tap(find.byKey(const Key('nav-matches')));
    await tester.pumpAndSettle();

    expect(find.text('WEEKEND WARRIORS'), findsOneWidget);
    expect(find.text('OFFICE XI'), findsOneWidget);
    expect(find.text('TITANS'), findsOneWidget);
    expect(find.textContaining('CONTINUE'), findsWidgets);
  });

  testWidgets('create match opens format step with defaults', (tester) async {
    await pumpManagementApp(tester, teams: _twoTeams());
    await _go(tester, AppRoutes.matchNew);

    expect(find.text('SELECT FORMAT'), findsOneWidget);
    expect(find.byKey(const Key('format-t10')), findsOneWidget);
    expect(find.byKey(const Key('format-t20')), findsOneWidget);
    expect(find.byKey(const Key('format-odi')), findsOneWidget);
    expect(find.byKey(const Key('format-custom')), findsOneWidget);
    expect(find.text('10 OVERS'), findsOneWidget);
    expect(find.text('20 OVERS'), findsOneWidget);
    expect(find.text('50 OVERS'), findsOneWidget);
    expect(find.text('CHOOSE YOUR SETUP'), findsOneWidget);
  });

  testWidgets('selecting formats keeps visible default overs', (tester) async {
    await pumpManagementApp(tester, teams: _twoTeams());
    await _go(tester, AppRoutes.matchNew);

    await tester.tap(find.byKey(const Key('format-t10')));
    await tester.pump();
    expect(find.byKey(const Key('format-t10')), findsOneWidget);

    await tester.tap(find.byKey(const Key('format-odi')));
    await tester.pump();
    expect(find.text('50 OVERS'), findsOneWidget);

    await tester.tap(find.byKey(const Key('format-custom')));
    await tester.pump();
    expect(find.text('CHOOSE YOUR SETUP'), findsOneWidget);
  });

  testWidgets('fewer than two teams shows useful empty state', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(teams: [sampleTeam()]),
    );
    await _go(tester, AppRoutes.matchNew);
    await tester.tap(find.byKey(const Key('format-t20')));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    expect(find.text('You need two teams'), findsOneWidget);
    expect(find.byKey(const Key('manage-teams')), findsOneWidget);
  });

  testWidgets('same team cannot be chosen twice', (tester) async {
    await pumpManagementApp(tester, teams: _twoTeams());
    await _go(tester, AppRoutes.matchNew);
    await tester.tap(find.byKey(const Key('format-t20')));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('team-a-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('WEEKEND WARRIORS').last);
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('team-b-selector')));
    await tester.pumpAndSettle();
    expect(find.text('WEEKEND WARRIORS'), findsNothing);
    expect(find.text('OFFICE XI'), findsOneWidget);
    await tester.tap(find.text('OFFICE XI'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();
    expect(find.text('MATCH SETTINGS'), findsOneWidget);
  });

  testWidgets('custom overs out of range are rejected', (tester) async {
    await pumpManagementApp(tester, teams: _twoTeams());
    await _go(tester, AppRoutes.matchNew);
    await tester.tap(find.byKey(const Key('format-custom')));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('team-a-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('WEEKEND WARRIORS').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('team-b-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('OFFICE XI'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('overs-field')), '0');
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pump();
    expect(find.text('Custom overs must be between 1 and 50.'), findsOneWidget);
  });

  testWidgets('playing XI count captain keeper toss and ready', (tester) async {
    final matches = FakeMatchRepository();
    await pumpManagementApp(tester, teams: _twoTeams(), matches: matches);
    await _go(tester, AppRoutes.matchNew);
    await tester.tap(find.byKey(const Key('format-t20')));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('team-a-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('WEEKEND WARRIORS').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('team-b-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('OFFICE XI'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('players-per-team-field')),
      '8',
    );
    await tester.enterText(
      find.byKey(const Key('venue-field')),
      'Central Ground',
    );
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    expect(find.text('SELECTED 0 / 8'), findsOneWidget);
    await tester.tap(find.byKey(const Key('select-all-xi')));
    await tester.pump();
    expect(find.text('SELECTED 8 / 8'), findsOneWidget);
    await tester.tap(find.text('CAPTAIN').first);
    await tester.tap(find.text('KEEPER').at(1));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('select-all-xi')));
    await tester.pump();
    await tester.tap(find.text('CAPTAIN').first);
    await tester.tap(find.text('KEEPER').at(1));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('toss-team-a')));
    await tester.tap(find.byKey(const Key('toss-bat')));
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    expect(find.textContaining('elected to bat'), findsOneWidget);
    await tester.tap(find.byKey(const Key('continue-setup')));
    await tester.pumpAndSettle();

    expect(find.text('Match ready'), findsOneWidget);
    expect(
      find.text('Select opening players and start live scoring.'),
      findsOneWidget,
    );
    expect(matches.details.values.single.status, MatchStatus.ready);
  });

  testWidgets('draft restoration reloads saved teams', (tester) async {
    final teams = _twoTeams();
    final matches = FakeMatchRepository(
      matches: [
        sampleMatch(
          id: 'match-draft',
          status: MatchStatus.draft,
          playersPerTeam: 8,
          teams: [
            sampleMatchTeam(
              id: 'mt-a',
              teamId: 'team-1',
              side: MatchSide.teamA,
              name: 'Weekend Warriors',
            ),
            sampleMatchTeam(
              id: 'mt-b',
              teamId: 'team-2',
              side: MatchSide.teamB,
              name: 'Office XI',
            ),
          ],
        ),
      ],
    );
    await pumpManagementApp(tester, teams: teams, matches: matches);
    await _go(tester, AppRoutes.matchSetup('match-draft'));

    expect(find.text('MATCH SETTINGS'), findsOneWidget);
    expect(find.byKey(const Key('players-per-team-field')), findsOneWidget);
    final router = GoRouter.of(tester.element(find.text('MATCH SETTINGS')));
    router.go(AppRoutes.matches);
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('CONTINUE'));
    await tester.pumpAndSettle();
    expect(find.text('MATCH SETTINGS'), findsOneWidget);
  });

  testWidgets('review shows missing configuration', (tester) async {
    final matches = FakeMatchRepository(
      matches: [
        sampleMatch(
          id: 'match-draft',
          status: MatchStatus.draft,
          playersPerTeam: 8,
          teams: [
            sampleMatchTeam(
              id: 'mt-a',
              teamId: 'team-1',
              side: MatchSide.teamA,
              name: 'Weekend Warriors',
              players: [
                const MatchPlayer(
                  playerId: 'A-p-1',
                  name: 'A Player 1',
                  isPlaying: true,
                  isCaptain: true,
                  isWicketKeeper: true,
                  battingPosition: 1,
                ),
              ],
            ),
            sampleMatchTeam(
              id: 'mt-b',
              teamId: 'team-2',
              side: MatchSide.teamB,
              name: 'Office XI',
            ),
          ],
        ),
      ],
    );
    await pumpManagementApp(tester, teams: _twoTeams(), matches: matches);
    await _go(tester, AppRoutes.match('match-draft'));
    expect(find.textContaining('Playing XI requires 8 players'), findsWidgets);
    expect(find.byKey(const Key('continue-setup')), findsOneWidget);
  });
}
