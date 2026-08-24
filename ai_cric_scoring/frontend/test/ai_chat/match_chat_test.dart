import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:ai_cric_scoring/features/ai_chat/data/models/match_chat.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_chat_repo.dart';
import '../helpers/fake_match_repo.dart';
import '../helpers/pump_app.dart';

MatchDetail _completed({String id = 'match-done'}) {
  return sampleMatch(
    id: id,
    name: 'Sunday Final',
    status: MatchStatus.completed,
    format: MatchFormat.t20,
    venueName: 'Central Ground',
    completedAt: DateTime.utc(2026, 8, 12, 13),
    teams: [
      sampleMatchTeam(
        id: 'mt-a-$id',
        teamId: 'team-1',
        side: MatchSide.teamA,
        name: 'Weekend Warriors',
      ),
      sampleMatchTeam(
        id: 'mt-b-$id',
        teamId: 'team-2',
        side: MatchSide.teamB,
        name: 'Office XI',
      ),
    ],
    result: const MatchResultSummary(
      type: MatchResultType.won,
      winnerMatchTeamId: 'mt-a-match-done',
      winnerName: 'Weekend Warriors',
      marginRuns: 12,
      summary: 'Weekend Warriors won by 12 runs',
    ),
  );
}

MatchDetail _status(MatchStatus status) {
  return sampleMatch(
    id: 'match-${status.apiValue.toLowerCase()}',
    status: status,
    teams: [
      sampleMatchTeam(
        id: 'mt-a',
        teamId: 'team-1',
        side: MatchSide.teamA,
        name: 'A',
      ),
      sampleMatchTeam(
        id: 'mt-b',
        teamId: 'team-2',
        side: MatchSide.teamB,
        name: 'B',
      ),
    ],
  );
}

Future<void> _open(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(Navigator).first);
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('completed match detail shows match chat CTA', (tester) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
    );
    await _open(tester, AppRoutes.match('match-done'));
    await tester.scrollUntilVisible(
      find.byKey(const Key('open-match-chat')),
      200,
    );
    expect(find.byKey(const Key('open-match-chat')), findsOneWidget);
  });

  testWidgets('non-completed matches do not show match chat CTA', (
    tester,
  ) async {
    for (final status in [
      MatchStatus.draft,
      MatchStatus.ready,
      MatchStatus.live,
    ]) {
      await pumpCricketApp(
        tester,
        matches: FakeMatchRepository(matches: [_status(status)]),
      );
      await _open(
        tester,
        AppRoutes.match('match-${status.apiValue.toLowerCase()}'),
      );
      expect(find.byKey(const Key('open-match-chat')), findsNothing);
    }
  });

  testWidgets('empty chat shows suggestions then sending state', (
    tester,
  ) async {
    final repo = FakeMatchChatRepository(
      sendDelay: const Duration(milliseconds: 80),
    );
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      chat: repo,
    );
    await _open(tester, AppRoutes.matchChat('match-done'));
    expect(find.text('TRY ASKING'), findsOneWidget);
    await tester.tap(find.byKey(const Key('suggest-1')));
    await tester.pump();
    expect(find.byKey(const Key('analyzing-match')), findsOneWidget);
    await tester.pumpAndSettle();
    expect(find.text('Weekend Warriors won by 12 runs.'), findsWidgets);
    expect(repo.sendCalls, 1);
  });

  testWidgets('chat renders analytical evidence and clarification', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      chat: FakeMatchChatRepository(
        messages: [
          sampleUserMessage(content: 'Why did Warriors lose?'),
          sampleAssistantMessage(
            content:
                'Warriors lost mainly because three wickets fell in the middle overs.',
            answerType: ChatAnswerType.analytical,
            evidence: const [
              ChatEvidence(
                factId: 'fow_2_3',
                type: 'fall_of_wicket',
                label: 'Wicket cluster',
                summary: '3 wickets fell between overs 12.2 and 14.1',
              ),
            ],
          ),
        ],
      ),
    );
    await _open(tester, AppRoutes.matchChat('match-done'));
    expect(find.text('AI / MATCH INTELLIGENCE'), findsWidgets);
    expect(find.textContaining('3 WICKETS'), findsWidgets);
    await tester.enterText(
      find.byKey(const Key('chat-input')),
      'How many did Rahul score?',
    );
    await tester.tap(find.byKey(const Key('send-chat')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Which Rahul do you mean'), findsOneWidget);
    expect(find.byKey(const Key('clarify-Rahul Shah')), findsOneWidget);
  });

  testWidgets('generation error shows retry without inventing an answer', (
    tester,
  ) async {
    final repo = FakeMatchChatRepository(
      generationError: const ChatGenerationError(
        code: 'AI_TIMEOUT',
        message:
            "Your question was saved, but I couldn't generate the AI answer right now.",
      ),
    );
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      chat: repo,
    );
    await _open(tester, AppRoutes.matchChat('match-done'));
    await tester.enterText(
      find.byKey(const Key('chat-input')),
      'Why did Office XI lose?',
    );
    await tester.tap(find.byKey(const Key('send-chat')));
    await tester.pumpAndSettle();
    expect(find.textContaining('couldn\'t generate'), findsOneWidget);
    expect(find.byKey(const Key('retry-chat')), findsOneWidget);
  });

  testWidgets('chat supports light and dark themes and tablet width', (
    tester,
  ) async {
    for (final mode in [ThemeMode.light, ThemeMode.dark]) {
      await pumpCricketApp(
        tester,
        size: const Size(1024, 768),
        matches: FakeMatchRepository(matches: [_completed()]),
        chat: FakeMatchChatRepository(
          messages: [sampleUserMessage(), sampleAssistantMessage()],
        ),
        overrides: [themeModeProvider.overrideWith(() => _FixedTheme(mode))],
      );
      await _open(tester, AppRoutes.matchChat('match-done'));
      expect(find.text('AI / MATCH CHAT'), findsOneWidget);
      expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
    }
  });
}

class _FixedTheme extends ThemeModeController {
  _FixedTheme(this._mode);
  final ThemeMode _mode;
  @override
  ThemeMode build() => _mode;
}
