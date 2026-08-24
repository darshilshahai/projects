import 'package:ai_cric_scoring/app/app.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/pump_app.dart';

void main() {
  testWidgets('app starts on Home with Cricket Intelligence', (tester) async {
    await pumpCricketApp(tester);

    expect(find.text('CRICKET INTELLIGENCE'), findsOneWidget);
    expect(find.text('START NEW MATCH'), findsOneWidget);
  });

  testWidgets('CricketIntelligenceApp constructs without error', (
    tester,
  ) async {
    await pumpCricketApp(tester);
    expect(find.byType(CricketIntelligenceApp), findsOneWidget);
  });
}
