# C++: contracts to preserve

## Resolve the target

Inspect CMake/build manifests, supported C++ standard, compiler/standard library, ABI and exception/RTTI policy. Do not force a newer dialect or dependency into an existing target.

## Apply at the affected boundary

- Use RAII and owning standard containers or `unique_ptr` by default where they match the interface. Prefer the rule of zero, and document non-owning pointer and reference lifetimes.
- string_view and span borrow storage; they do not extend its lifetime. Check invalidation from reallocation, moves and escaping callbacks. Pushing to a vector inside a range-for over it is undefined when it reallocates.
- Preserve exception guarantees and project error policy. Destructors are `noexcept` by default, so an escaping exception calls `std::terminate`. Declare a move `noexcept` only when its implementation and member/base moves cannot throw. Prefer defaulted exception inference or an accurate conditional specification such as `noexcept(std::is_nothrow_move_constructible_v<Member>)` for a single-member move. An unconditional promise on a throwing move terminates instead of preserving a catchable exception. Vector reallocation may copy to preserve its exception guarantee; correctness comes before suppressing that copy.
- Keep locks scoped to the complete invariant and avoid callbacks or blocking I/O under them. shared_ptr does not synchronize the pointed-to state and can form retention cycles.

## Worked failure and correction

A returned view must not refer to a temporary:

```cpp
// Return owned text when construction happens inside the function.
std::string display_name(const User& user) {
    return user.first + " " + user.last;
}
```

Returning string_view here would borrow destroyed storage. A view suits a caller
that owns stable backing storage for the full use interval.

## Traps to check

- Choose captures from the actual lifetime and synchronization contract. A stored/escaping callback must not outlive referenced locals; capture values or suitable owning state when it can escape. A joined worker may safely capture a parent-owned result by reference if the object survives every use and reads occur after join (or under suitable synchronization). Capturing that result by value updates a copy and loses the intended output. Join on every exit path, and protect concurrent accesses; value capture alone does not make borrowed pointers or shared state safe.
- Destroying a joinable `std::thread` calls `std::terminate`. Use `std::jthread` from C++20, or join on every path.
- `map[key]` inserts a default value when the key is missing. Use `find` or `contains` for lookups.
- `vector::reserve` changes capacity, not size: writing `v[0]` into an empty reserved vector is invalid. Use push, emplace or resize.
- `std::move` on a const object silently copies. Standard-library moved-from objects are valid but unspecified; do not assume empty.
- Mark single-argument constructors `explicit` unless the implicit conversion is intended.

## Evidence to report

Use the configured compiler/format/analyzer and authorized sanitizer or concurrency checks for the changed path. A clean build does not establish ABI compatibility or lifetime safety.

## Primary references

Reviewed 24 October 2026: [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines), [Clang address sanitizer](https://clang.llvm.org/docs/AddressSanitizer.html).

Focused semantics reviewed 30 October 2026: [C++ vector capacity](https://eel.is/c++draft/vector.capacity), [moved-from library types](https://eel.is/c++draft/lib.types.movedfrom).

Reviewed 1 November 2026: [std::jthread](https://en.cppreference.com/w/cpp/thread/jthread.html).
