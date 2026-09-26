import 'package:flutter_test/flutter_test.dart';
import 'package:aquaguard_field/main.dart';

void main() {
  testWidgets('AquaGuard Field app bootstrap test', (WidgetTester tester) async {
    await tester.pumpWidget(const AquaGuardFieldApp());
    expect(find.byType(AquaGuardFieldApp), findsOneWidget);
  });
}
