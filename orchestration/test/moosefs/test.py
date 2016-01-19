from orchestration.moosefs.commands import Moosefs

nap_volume = Moosefs('mongo', 'mongo')
print nap_volume.volume
