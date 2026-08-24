import 'package:ai_cric_scoring/app/app.dart';
import 'package:ai_cric_scoring/features/ai_analysis/data/repositories/match_analysis_repository.dart';
import 'package:ai_cric_scoring/features/ai_analysis/presentation/controllers/match_analysis_controller.dart';
import 'package:ai_cric_scoring/features/ai_chat/data/repositories/match_chat_repository.dart';
import 'package:ai_cric_scoring/features/analytics/data/repositories/analytics_repository.dart';
import 'package:ai_cric_scoring/features/analytics/presentation/controllers/analytics_controllers.dart';
import 'package:ai_cric_scoring/features/ai_chat/presentation/controllers/match_chat_controller.dart';
import 'package:ai_cric_scoring/features/auth/presentation/providers/auth_providers.dart';
import 'package:ai_cric_scoring/features/matches/data/repositories/match_repository.dart';
import 'package:ai_cric_scoring/features/matches/presentation/controllers/match_providers.dart';
import 'package:ai_cric_scoring/features/players/data/repositories/player_repository.dart';
import 'package:ai_cric_scoring/features/players/presentation/controllers/player_providers.dart';
import 'package:ai_cric_scoring/features/scorecard/data/repositories/scorecard_repository.dart';
import 'package:ai_cric_scoring/features/scorecard/presentation/controllers/scorecard_controller.dart';
import 'package:ai_cric_scoring/features/scoring/data/repositories/scoring_repository.dart';
import 'package:ai_cric_scoring/features/scoring/presentation/controllers/live_scoring_controller.dart';
import 'package:ai_cric_scoring/features/teams/data/repositories/team_repository.dart';
import 'package:ai_cric_scoring/features/teams/presentation/controllers/team_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'auth_controllers.dart';
import 'fake_analysis_repo.dart';
import 'fake_analytics_repo.dart';
import 'fake_chat_repo.dart';
import 'fake_management_repos.dart';
import 'fake_match_repo.dart';
import 'fake_scorecard_repo.dart';
import 'fake_scoring_repo.dart';

Future<void> pumpCricketApp(
  WidgetTester tester, {
  Size size = const Size(390, 844),
  List<Override> overrides = const [],
  TeamRepository? teams,
  PlayerRepository? players,
  MatchRepository? matches,
  ScoringRepository? scoring,
  ScorecardRepository? scorecard,
  MatchAnalysisRepository? analysis,
  MatchChatRepository? chat,
  AnalyticsRepository? analytics,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(AuthenticatedAuthController.new),
        if (teams != null) teamRepositoryProvider.overrideWithValue(teams),
        if (players != null)
          playerRepositoryProvider.overrideWithValue(players),
        matchRepositoryProvider.overrideWithValue(
          matches ?? FakeMatchRepository(),
        ),
        scoringRepositoryProvider.overrideWithValue(
          scoring ?? FakeScoringRepository(),
        ),
        scorecardRepositoryProvider.overrideWithValue(
          scorecard ?? FakeScorecardRepository(),
        ),
        matchAnalysisRepositoryProvider.overrideWithValue(
          analysis ?? FakeMatchAnalysisRepository(),
        ),
        matchChatRepositoryProvider.overrideWithValue(
          chat ?? FakeMatchChatRepository(),
        ),
        analyticsRepositoryProvider.overrideWithValue(
          analytics ?? FakeAnalyticsRepository(),
        ),
        ...overrides,
      ],
      child: const CricketIntelligenceApp(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> pumpManagementApp(
  WidgetTester tester, {
  FakeTeamRepository? teams,
  FakePlayerRepository? players,
  FakeMatchRepository? matches,
  ScoringRepository? scoring,
  ScorecardRepository? scorecard,
  MatchAnalysisRepository? analysis,
  MatchChatRepository? chat,
  AnalyticsRepository? analytics,
  List<Override> overrides = const [],
  Size size = const Size(390, 844),
}) {
  final resolvedTeams = teams ?? FakeTeamRepository();
  final resolvedMatches = matches ?? FakeMatchRepository();
  resolvedMatches.teams.addAll({
    for (final team in resolvedTeams.teams) team.id: team,
  });
  for (final entry in resolvedTeams.rosterByTeam.entries) {
    resolvedMatches.rosterByTeam.putIfAbsent(entry.key, () => entry.value);
  }
  return pumpCricketApp(
    tester,
    teams: resolvedTeams,
    players: players ?? FakePlayerRepository(),
    matches: resolvedMatches,
    scoring: scoring,
    scorecard: scorecard,
    analysis: analysis,
    chat: chat,
    analytics: analytics,
    overrides: overrides,
    size: size,
  );
}
