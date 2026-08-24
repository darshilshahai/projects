import 'package:ai_cric_scoring/core/shell/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/pump_app.dart';

void main() {
  testWidgets('phone shell uses NavigationBar', (tester) async {
    await pumpCricketApp(tester, size: const Size(390, 844));

    expect(find.byKey(navigationBarKey), findsOneWidget);
    expect(find.byKey(navigationRailKey), findsNothing);
  });

  testWidgets('tablet shell uses NavigationRail', (tester) async {
    await pumpCricketApp(tester, size: const Size(800, 1024));

    expect(find.byKey(navigationRailKey), findsOneWidget);
    expect(find.byKey(navigationBarKey), findsNothing);
  });

  testWidgets('bottom navigation switches shell branches', (tester) async {
    await pumpCricketApp(tester, size: const Size(390, 844));

    await tester.tap(find.byKey(const Key('nav-matches')));
    await tester.pumpAndSettle();
    expect(find.text('Desk.'), findsOneWidget);

    await tester.tap(find.byKey(const Key('nav-ai')));
    await tester.pumpAndSettle();
    expect(find.text('AI MATCH'), findsOneWidget);

    await tester.tap(find.byKey(const Key('nav-stats')));
    await tester.pumpAndSettle();
    expect(find.text('Terminal.'), findsOneWidget);

    await tester.tap(find.byKey(const Key('nav-profile')));
    await tester.pumpAndSettle();
    expect(find.text('Preferences.'), findsOneWidget);

    await tester.tap(find.byKey(const Key('nav-home')));
    await tester.pumpAndSettle();
    expect(find.text('START NEW MATCH'), findsOneWidget);
  });

  testWidgets('home has no overflow at phone size', (tester) async {
    await pumpCricketApp(tester, size: const Size(390, 844));
    expect(tester.takeException(), isNull);
    expect(find.text('START NEW MATCH'), findsOneWidget);
  });
}
