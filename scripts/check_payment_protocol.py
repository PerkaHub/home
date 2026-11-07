"""Executable design model, not an application or a provider integration test."""
from dataclasses import dataclass, replace
from itertools import product

@dataclass(frozen=True)
class Attempt:
    status: str = 'created'
    provider_status: str = 'absent'
    external_operations: int = 0
    settlements: int = 0
    replay_allowed: bool = True
    reconciliation_required: bool = False

FINAL = {'succeeded', 'rejected'}

def apply_final(a, status):
    if a.status in FINAL:
        return replace(a, reconciliation_required=a.reconciliation_required or a.status != status)
    return replace(a, status=status, settlements=a.settlements + int(status == 'succeeded'))

def step(a, event):
    if event == 'dispatch':
        if a.status not in FINAL and a.replay_allowed and a.provider_status == 'absent':
            return replace(a, provider_status='pending', external_operations=a.external_operations + 1)
        return a
    if event == 'create_ack':
        return replace(a, status='pending') if a.status == 'created' and a.provider_status != 'absent' else a
    if event == 'timeout':
        return replace(a, status='pending') if a.status == 'created' else a
    if event == 'provider_success':
        return replace(a, provider_status='succeeded') if a.provider_status != 'absent' else a
    if event in ('webhook_success', 'webhook_rejected'):
        if a.provider_status == 'absent':
            return a
        final = 'succeeded' if event == 'webhook_success' else 'rejected'
        return apply_final(replace(a, provider_status=final), final)
    if event == 'expire_replay':
        return replace(a, replay_allowed=False)
    if event == 'worker':
        if a.status in FINAL:
            return a
        if a.provider_status in FINAL:
            return apply_final(a, a.provider_status)
        if a.provider_status == 'absent':
            if not a.replay_allowed:
                return replace(a, reconciliation_required=True)
            a = step(a, 'dispatch')
        return replace(a, status='pending')
    raise ValueError(event)

def run(events):
    a = Attempt()
    for event in events:
        previous = a
        a = step(a, event)
        assert a.external_operations <= 1, (events, a)
        assert a.settlements <= 1, (events, a)
        if previous.status in FINAL:
            assert a.status == previous.status, (events, a)
    return a

def main():
    # Crash after commit, before network: durable created is picked up by worker.
    a = run(['worker'])
    assert a.status == 'pending' and a.external_operations == 1
    # Crash after provider accepted, before db ack: retry must not create another operation.
    a = run(['dispatch', 'worker', 'dispatch', 'worker'])
    assert a.status == 'pending' and a.external_operations == 1
    # Provider completed while process was down; recovery observes the result.
    a = run(['dispatch', 'provider_success', 'worker'])
    assert a.status == 'succeeded' and a.settlements == 1
    # Early webhook wins over a late create ack and timeout.
    a = run(['dispatch', 'webhook_success', 'create_ack', 'timeout', 'worker'])
    assert a.status == 'succeeded' and a.settlements == 1
    # Repeated webhook and contradictory final do not settle twice or downgrade.
    a = run(['dispatch', 'webhook_success', 'webhook_success', 'webhook_rejected'])
    assert a.status == 'succeeded' and a.settlements == 1 and a.reconciliation_required
    # No replay beyond the provider's key retention window.
    a = run(['expire_replay', 'worker', 'dispatch'])
    assert a.external_operations == 0 and a.reconciliation_required
    events = ['dispatch', 'create_ack', 'timeout', 'provider_success', 'webhook_success', 'webhook_rejected', 'expire_replay', 'worker']
    count = 0
    for sequence in product(events, repeat=5):
        run(sequence)
        count += 1
    print(f'PASS: 6 recovery scenarios and {count} event sequences in the design model')
    print('Scope: assumes durable transactions, eventual worker execution and provider idempotency; not an integration test')

if __name__ == '__main__':
    main()
