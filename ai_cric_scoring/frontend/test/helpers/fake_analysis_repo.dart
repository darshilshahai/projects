import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/ai_analysis/data/models/match_analysis.dart';
import 'package:ai_cric_scoring/features/ai_analysis/data/repositories/match_analysis_repository.dart';

MatchAnalysis sampleAnalysis({
  String headline = "Warriors' middle-order partnership decides tight chase",
  String summary =
      'A strong middle-overs partnership stabilized the innings after two early wickets. The bowling side created pressure but could not force a collapse.',
  String potmName = 'Rahul Shah',
}) {
  const partnership = AnalysisEvidence(
    factId: 'pship_1_1',
    type: 'partnership',
    label: 'Rahul Shah / Dev Patel',
    summary: 'Rahul Shah and Dev Patel added 68 runs from 43 legal balls.',
  );
  const batting = AnalysisEvidence(
    factId: 'bat_1_rahul',
    type: 'batting',
    label: 'Rahul Shah',
    summary: 'Rahul Shah 62 (41), 4s 6, 6s 2, SR 151.22',
  );
  const turning = AnalysisPoint(
    title: 'Middle-order stand',
    insight: 'This stabilized the innings after two early wickets.',
    importance: 'HIGH',
    eventType: 'PARTNERSHIP',
    evidence: [partnership],
  );
  return MatchAnalysis(
    headline: headline,
    summary: summary,
    winningFactors: const [
      AnalysisPoint(
        title: 'Middle-order stability',
        insight: 'The third-wicket stand rebuilt the innings.',
        importance: 'HIGH',
        evidence: [partnership],
      ),
    ],
    losingFactors: const [
      AnalysisPoint(
        title: 'Late wickets',
        insight: 'Wickets in the closing phase reduced momentum.',
        importance: 'MEDIUM',
        evidence: [
          AnalysisEvidence(
            factId: 'fow_2_3',
            type: 'fall_of_wicket',
            label: '3-120 Dev Patel',
            summary: 'Wicket 3: Dev Patel at 120 in over 14.2.',
          ),
        ],
      ),
    ],
    battingAnalysis: const [
      AnalysisPoint(
        title: 'Rahul Shah',
        insight: 'Anchored the chase through the middle overs.',
        importance: 'HIGH',
        matchPlayerName: 'Rahul Shah',
        evidence: [batting],
      ),
    ],
    bowlingAnalysis: const [
      AnalysisPoint(
        title: 'Dev Mehta',
        insight: 'Took the new ball and created early pressure.',
        importance: 'MEDIUM',
        matchPlayerName: 'Dev Mehta',
        evidence: [
          AnalysisEvidence(
            factId: 'bowl_1_dev',
            type: 'bowling',
            label: 'Dev Mehta',
            summary: 'Dev Mehta 4.0-0-28-2, econ 7.0',
          ),
        ],
      ),
    ],
    partnershipAnalysis: const [turning],
    turningPoints: const [turning],
    recommendations: const [
      AnalysisPoint(
        title: 'Protect the middle overs',
        insight: 'Keep a set batter through overs 7-12 after early wickets.',
        importance: 'HIGH',
        evidence: [partnership],
      ),
    ],
    playerOfMatch: PlayerOfMatchRecommendation(
      matchPlayerId: 'mp-rahul',
      name: potmName,
      reason: 'Anchored the innings and featured in the decisive partnership.',
      confidence: 'HIGH',
      evidence: const [batting],
    ),
    metadata: AnalysisMetadata(
      generatedAt: DateTime.utc(2026, 8, 15, 10),
      provider: 'fake',
      model: 'fake-model',
      analysisVersion: 'v1',
      promptVersion: 'match_analysis_v1',
      factsVersion: 'scorecard_v1',
    ),
  );
}

class FakeMatchAnalysisRepository implements MatchAnalysisRepository {
  FakeMatchAnalysisRepository({
    this.analysis,
    this.generateError,
    this.generateDelay,
  });

  MatchAnalysis? analysis;
  Object? generateError;
  int generateCalls = 0;
  int regenerateCalls = 0;
  Duration? generateDelay;

  @override
  Future<MatchAnalysis?> getAnalysis(String matchId) async {
    return analysis;
  }

  @override
  Future<MatchAnalysis> generateAnalysis(String matchId) async {
    generateCalls += 1;
    if (generateDelay != null) {
      await Future<void>.delayed(generateDelay!);
    }
    if (generateError != null) {
      throw generateError!;
    }
    analysis = sampleAnalysis();
    return analysis!;
  }

  @override
  Future<MatchAnalysis> regenerateAnalysis(String matchId) async {
    regenerateCalls += 1;
    if (generateError != null) {
      throw generateError!;
    }
    analysis = sampleAnalysis(headline: 'Regenerated grounded headline');
    return analysis!;
  }
}

ApiException analysisUnavailable() {
  return const ApiException(
    'Unable to generate analysis right now.',
    statusCode: 502,
    code: 'AI_PROVIDER_ERROR',
  );
}
