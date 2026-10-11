from manufacturing_process_optimization.case04_worker_rotation import (
    demo_instance,
    optimize_rotation,
)


def test_rotation_staffs_every_station_period():
    workers, stations = demo_instance()
    periods = 4
    result = optimize_rotation(workers, stations, periods=periods)
    assert len(result.assignment) == periods * len(stations)
    for (period, station), worker_name in result.assignment.items():
        worker = next(w for w in workers if w.name == worker_name)
        assert station in worker.qualified_stations
        assert 0 <= period < periods
