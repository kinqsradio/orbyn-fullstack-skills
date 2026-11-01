// Synthetic C++17 controls for move exception guarantees and joined result capture.
#include <cstdlib>
#include <exception>
#include <iostream>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>

struct ThrowingMember {
    ThrowingMember() = default;
    ThrowingMember(ThrowingMember&&) { throw 7; }
};

struct ConditionalMove {
    ThrowingMember member;
    ConditionalMove() = default;
    ConditionalMove(ConditionalMove&& other)
        noexcept(std::is_nothrow_move_constructible_v<ThrowingMember>)
        : member(std::move(other.member)) {}
};

struct InferredMove {
    ThrowingMember member;
    InferredMove() = default;
    InferredMove(InferredMove&&) = default;
};

struct NonthrowingMember { NonthrowingMember(NonthrowingMember&&) noexcept = default; };
struct NonthrowingRecord { NonthrowingMember member; };

// Deliberately incorrect negative control: the member's exception terminates.
struct UnconditionalMove {
    ThrowingMember member;
    UnconditionalMove() = default;
    UnconditionalMove(UnconditionalMove&& other) noexcept
        : member(std::move(other.member)) {}
};

int main(int argc, char** argv) {
    static_assert(!std::is_nothrow_move_constructible_v<ConditionalMove>);
    static_assert(!std::is_nothrow_move_constructible_v<InferredMove>);
    static_assert(std::is_nothrow_move_constructible_v<NonthrowingRecord>);
    if (argc != 2) return 2;
    const std::string mode = argv[1];
    std::set_terminate([] { std::_Exit(42); });
    if (mode == "conditional" || mode == "inferred" || mode == "unconditional") {
        try {
            if (mode == "conditional") { ConditionalMove source; ConditionalMove target(std::move(source)); }
            if (mode == "inferred") { InferredMove source; InferredMove target(std::move(source)); }
            if (mode == "unconditional") { UnconditionalMove source; UnconditionalMove target(std::move(source)); }
        } catch (int code) {
            std::cout << "caught " << code << '\n';
            return code == 7 ? 0 : 3;
        }
        return 4;
    }
    int result = 0;
    if (mode == "reference") {
        // result outlives the worker; join synchronizes its write with this read.
        std::thread worker([&result] { result = 42; });
        worker.join();
    } else if (mode == "value") {
        std::thread worker([result]() mutable { result = 42; });
        worker.join();
    } else return 2;
    std::cout << result << '\n';
}
