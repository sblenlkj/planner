scheduler = AsyncIOScheduler(timezone="UTC")

api_scheduler_adapter = ApschedulerApiSchedulerAdapter(
    scheduler=scheduler,
)

# container получает api_scheduler_adapter как ApiSchedulerPort
container = build_container(
    api_scheduler=api_scheduler_adapter,
)

direttore = build_direttore(container)

api_scheduler_adapter.bind_direttore(direttore)

scheduler.start()