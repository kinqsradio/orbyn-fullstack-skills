import Foundation
final class Box { var value: Int; init(_ value: Int) { self.value = value } }
struct Snapshot { var box: Box }
protocol Required { func value() -> String }
extension Required { func value() -> String { "default" }; func extra() -> String { "extension" } }
struct Concrete: Required { func value() -> String { "concrete" }; func extra() -> String { "concrete-extra" } }
actor RevisionStore {
  private var generation = 0
  private var value = "initial"
  func begin() -> Int { generation += 1; return generation }
  func finish(_ owner: Int, _ next: String) -> Bool { guard owner == generation else {return false}; value = next; return true }
  func current() -> String { value }
}
// Small callback adapter: one winner, including cancellation before attach.
final class Once: @unchecked Sendable {
  private let lock = NSLock()
  private var continuation: CheckedContinuation<Int, Error>?
  private var result: Result<Int, Error>?
  func attach(_ c: CheckedContinuation<Int, Error>) {
    lock.lock()
    if let ready = result { lock.unlock(); c.resume(with: ready); return }
    precondition(continuation == nil); continuation = c; lock.unlock()
  }
  func finish(_ next: Result<Int, Error>) {
    lock.lock(); guard result == nil else { lock.unlock(); return }
    result = next; let c = continuation; continuation = nil; lock.unlock(); c?.resume(with: next)
  }
}
@main struct Checks {
 static func main() async throws {
  let a=Snapshot(box: Box(1)); let b=a; b.box.value=2; precondition(a.box.value==2)
  let c=Concrete(); let p:any Required=c; precondition(p.value()=="concrete"); precondition(p.extra()=="extension"); precondition(c.extra()=="concrete-extra")
  let store=RevisionStore(); let old=await store.begin(), current=await store.begin()
  let stale=await store.finish(old,"wrong"), fresh=await store.finish(current,"right"), value=await store.current()
  precondition(!stale && fresh && value=="right")
  let early=Once();early.finish(.failure(CancellationError()));early.finish(.success(9))
  do { let _:Int=try await withCheckedThrowingContinuation {early.attach($0)};preconditionFailure("cancel must win") } catch is CancellationError {}
  let gate=Once();let result:Int=try await withCheckedThrowingContinuation { c in gate.attach(c);gate.finish(.success(7));gate.finish(.success(8)) };precondition(result==7)
  let taskGate=Once()
  let task=Task<Int,Error> {try await withTaskCancellationHandler {try await withCheckedThrowingContinuation {taskGate.attach($0)}} onCancel: {taskGate.finish(.failure(CancellationError()))}}
  task.cancel();do { _=try await task.value;preconditionFailure("cancelled task must fail") } catch is CancellationError {}
  print("PASS nested-reference, protocol-dispatch, actor-generation, callback-exactly-once, early-cancel, task-cancel")
 }
}
