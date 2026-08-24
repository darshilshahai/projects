import 'package:ai_cric_scoring/core/theme/app_colors.dart';
import 'package:ai_cric_scoring/core/theme/app_theme.dart';
import 'package:ai_cric_scoring/core/theme/app_theme_extensions.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'helpers/pump_app.dart';

void main() {
  test('light and dark themes construct with cricket extensions', () {
    final light = AppTheme.light;
    final dark = AppTheme.dark;

    expect(light.useMaterial3, isTrue);
    expect(dark.useMaterial3, isTrue);
    expect(light.extension<CricketColors>(), isNotNull);
    expect(dark.extension<AppSurfaces>(), isNotNull);
    expect(light.colorScheme.primary, AppColors.lime);
    expect(dark.colorScheme.primary, AppColors.lime);
    expect(
      light.extension<AppSurfaces>()!.background,
      isNot(dark.extension<AppSurfaces>()!.background),
    );
    expect(light.extension<AppSurfaces>()!.limeAccent, AppColors.lime);
  });

  testWidgets('theme selector switches to dark mode', (tester) async {
    await pumpCricketApp(tester, size: const Size(390, 844));

    await tester.tap(find.byKey(const Key('nav-profile')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('theme-dark')));
    await tester.pumpAndSettle();

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.themeMode, ThemeMode.dark);
  });

  testWidgets('themeModeProvider override renders dark theme', (tester) async {
    await pumpCricketApp(
      tester,
      overrides: [
        themeModeProvider.overrideWith(() {
          return _FixedThemeMode(ThemeMode.dark);
        }),
      ],
    );

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.themeMode, ThemeMode.dark);
    expect(find.text('START NEW MATCH'), findsOneWidget);
  });
}

class _FixedThemeMode extends ThemeModeController {
  _FixedThemeMode(this._mode);

  final ThemeMode _mode;

  @override
  ThemeMode build() => _mode;
}
