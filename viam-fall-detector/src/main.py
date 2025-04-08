import asyncio
from viam.module.module import Module
try:
    from models.fall import Fall
except ModuleNotFoundError:
    # when running as local module with run.sh
    from .models.fall import Fall


if __name__ == '__main__':
    asyncio.run(Module.run_from_registry())
