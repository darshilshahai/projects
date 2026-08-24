import 'package:ai_cric_scoring/core/theme/app_theme.dart';
import 'package:ai_cric_scoring/core/widgets/app_empty_state.dart';
import 'package:ai_cric_scoring/core/widgets/app_error_state.dart';
import 'package:ai_cric_scoring/core/widgets/app_status_badge.dart';
import 'package:ai_cric_scoring/core/widgets/score_display.dart';
import 'package:ai_cric_scoring/core/widgets/technical_label.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Widget _wrap(Widget child, {ThemeData? theme}) {
  return MaterialApp(
    theme: theme ?? AppTheme.light,
    darkTheme: AppTheme.dark,
    home: Scaffold(body: child),
  );
}

void main() {
  testWidgets('empty state renders title and action', (tester) async {
    await tester.pumpWidget(
      _wrap(
        AppEmptyState(
          title: 'No matches yet',
          description: 'Start a match to see it here.',
          action: FilledButton(onPressed: () {}, child: const Text('Action')),
        ),
      ),
    );

    expect(find.text('No matches yet'), findsOneWidget);
    expect(find.text('Start a match to see it here.'), findsOneWidget);
    expect(find.text('Action'), findsOneWidget);
  });

  testWidgets('error state renders retry without exposing internals', (
    tester,
  ) async {
    var retried = false;
    await tester.pumpWidget(
      _wrap(
        AppErrorState(
          message: AppErrorMessages.network,
          onRetry: () => retried = true,
        ),
      ),
    );

    expect(find.text('Something went wrong'), findsOneWidget);
    expect(find.text(AppErrorMessages.network), findsOneWidget);
    await tester.tap(find.text('Retry'));
    expect(retried, isTrue);
  });

  testWidgets('status badge renders label in light and dark', (tester) async {
    await tester.pumpWidget(
      _wrap(const AppStatusBadge(label: 'LIVE', tone: AppStatusTone.live)),
    );
    expect(find.text('LIVE'), findsOneWidget);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark,
        home: const Scaffold(
          body: AppStatusBadge(label: 'WON', tone: AppStatusTone.success),
        ),
      ),
    );
    expect(find.text('WON'), findsOneWidget);
  });

  testWidgets('score display and technical label render', (tester) async {
    await tester.pumpWidget(
      _wrap(
        const Column(
          children: [
            ScoreDisplay(score: '186/6', detail: '20.0 overs'),
            TechnicalLabel('Live match', showDot: true),
          ],
        ),
      ),
    );
    expect(find.text('186/6'), findsOneWidget);
    expect(find.text('20.0 OVERS'), findsOneWidget);
    expect(find.text('LIVE MATCH'), findsOneWidget);
  });
}
