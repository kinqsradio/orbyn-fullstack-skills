-------------------------- MODULE LeasedJob --------------------------
EXTENDS Naturals, TLC
CONSTANT Broken
VARIABLES phase, generation, owner, tokens, resultGeneration, resultWorker,
          publishCount, lateCancel
vars == <<phase, generation, owner, tokens, resultGeneration, resultWorker,
          publishCount, lateCancel>>
Init == /\ phase = "ready" /\ generation = 0 /\ owner = 0
        /\ tokens = <<0, 0>> /\ resultGeneration = 0 /\ resultWorker = 0
        /\ publishCount = 0 /\ lateCancel = FALSE
Claim(w) == /\ phase = "ready" /\ tokens[w] = 0 /\ generation < 2
            /\ generation' = generation + 1 /\ owner' = w /\ phase' = "leased"
            /\ tokens' = [tokens EXCEPT ![w] = generation + 1]
            /\ UNCHANGED <<resultGeneration, resultWorker, publishCount, lateCancel>>
Expire == /\ phase = "leased" /\ generation < 2
          /\ phase' = "ready" /\ owner' = 0
          /\ UNCHANGED <<generation, tokens, resultGeneration, resultWorker, publishCount, lateCancel>>
Complete(w) == /\ tokens[w] > 0
               /\ tokens' = [tokens EXCEPT ![w] = 0]
               /\ IF phase = "leased" /\ (Broken \/ (owner = w /\ tokens[w] = generation))
                     THEN /\ phase' = "done" /\ owner' = 0
                          /\ resultGeneration' = tokens[w] /\ resultWorker' = w
                     ELSE UNCHANGED <<phase, owner, resultGeneration, resultWorker>>
               /\ UNCHANGED <<generation, publishCount, lateCancel>>
Cancel == /\ phase \in {"ready", "leased"} /\ phase' = "cancelled" /\ owner' = 0
          /\ UNCHANGED <<generation, tokens, resultGeneration, resultWorker, publishCount, lateCancel>>
LateCancel == /\ phase = "done" /\ ~lateCancel /\ lateCancel' = TRUE
              /\ UNCHANGED <<phase, generation, owner, tokens, resultGeneration, resultWorker, publishCount>>
Publish == /\ phase = "done" /\ publishCount = 0 /\ publishCount' = 1
           /\ UNCHANGED <<phase, generation, owner, tokens, resultGeneration, resultWorker, lateCancel>>
Terminal == /\ (phase = "cancelled" \/ publishCount = 1) /\ UNCHANGED vars
Claim1 == Claim(1)
Claim2 == Claim(2)
Complete1 == Complete(1)
Complete2 == Complete(2)
Progress == Cancel \/ Complete1 \/ Complete2 \/ Publish
Next == Claim1 \/ Claim2 \/ Expire \/ Complete1 \/ Complete2 \/ Cancel \/ LateCancel \/ Publish \/ Terminal
Spec == Init /\ [][Next]_vars /\ WF_vars(Progress)
TypeOK == /\ phase \in {"ready", "leased", "done", "cancelled"}
          /\ generation \in 0..2 /\ owner \in 0..2 /\ tokens \in [1..2 -> 0..2]
          /\ resultGeneration \in 0..2 /\ resultWorker \in 0..2
          /\ publishCount \in 0..1 /\ lateCancel \in BOOLEAN
FreshResult == resultGeneration = 0 \/ resultGeneration = generation
CancelledHasNoResult == phase = "cancelled" => resultGeneration = 0 /\ publishCount = 0
PublishedFresh == publishCount = 1 => phase = "done" /\ resultGeneration = generation
EventuallyTerminal == <> (phase = "cancelled" \/ publishCount = 1)
=====================================================================
