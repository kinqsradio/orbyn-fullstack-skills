import XCTest
final class NativeWorkflowTests: XCTestCase {
 @MainActor func testRecoveryAndNavigation() {
  let app=XCUIApplication();app.launch()
  let switchAccount=app.buttons["Switch account"]
  XCTAssertTrue(switchAccount.waitForExistence(timeout: 30));switchAccount.tap()
  XCTAssertTrue(app.staticTexts["Account B"].waitForExistence(timeout: 10))
  let offline=app.switches["Offline fixture"];XCTAssertTrue(offline.exists);offline.tap()
  app.buttons["Retry"].tap()
  let status=app.staticTexts["status"]
  XCTAssertTrue(status.waitForExistence(timeout: 5))
  let offlineText=NSPredicate(format:"label CONTAINS %@", "Offline fixture — retry when ready")
  let condition=XCTNSPredicateExpectation(predicate:offlineText,object:status)
  XCTAssertEqual(XCTWaiter.wait(for:[condition],timeout:10),.completed)
  offline.tap();app.buttons["Retry"].tap()
  let item=app.descendants(matching:.any).matching(identifier:"Open B-0").firstMatch
  XCTAssertTrue(item.waitForExistence(timeout: 10));item.tap()
  XCTAssertTrue(app.staticTexts["Detail B-0"].waitForExistence(timeout: 10))
  let shot=XCTAttachment(screenshot:app.screenshot());shot.name="native-requested-detail";shot.lifetime = .keepAlways;add(shot)
 }
}
