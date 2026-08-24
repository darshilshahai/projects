import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('named formats expose default overs', () {
    expect(MatchFormat.t10.defaultOvers, 10);
    expect(MatchFormat.t20.defaultOvers, 20);
    expect(MatchFormat.odi.defaultOvers, 50);
    expect(MatchFormat.custom.defaultOvers, 20);
    expect(MatchFormat.t20.locksOvers, isTrue);
    expect(MatchFormat.custom.locksOvers, isFalse);
  });

  test('custom overs must stay within 1 and 50', () {
    bool valid(int overs) => overs >= 1 && overs <= 50;
    expect(valid(1), isTrue);
    expect(valid(50), isTrue);
    expect(valid(0), isFalse);
    expect(valid(51), isFalse);
  });
}
