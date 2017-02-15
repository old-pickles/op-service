import random
import string


BAD_WORDS = ["ass", "cock", "crap", "cunt", "fuck", "nigger", "piss", "pussy", "shit", "tits"]
SERVICE_INSTANCE_ID_LEN = 8


def _generate_service_instance_id():
  pool = string.ascii_lowercase + string.digits
  service_instance_id = ""
  for i in range(SERVICE_INSTANCE_ID_LEN):
    service_instance_id += random.choice(pool)
  for bad_word in BAD_WORDS:
    if bad_word in service_instance_id:
      return _generate_service_instance_id()
  return service_instance_id


SERVICE_INSTANCE_ID = _generate_service_instance_id()
