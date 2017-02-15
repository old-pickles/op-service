from functools import wraps
from threading import Semaphore, Thread


DEFAULT_THREAD_POOL_SIZE = 64


def async(thread_pool_size=DEFAULT_THREAD_POOL_SIZE):
  """
  A decorator that users the python 'Thread' object to run tasks asynchronously - note that because of the GIL, this
  decorator is only useful for non-compute tasks, like network calls. A call to the decorated function will return a
  special subclass of the thread object containing an 'await' function. Use this function to get the results of the
  asynchronous call (or throw the exception if there is one).

  Example 1 (will complete in 2 seconds because of the limitation on the thread_pool_size):
  @async(thread_pool_size=2)
  def test(i):
    import time
    time.sleep(1)
    return i
  threads = [test(i) for i in range(3)]
  results = [thread.await() for thread in threads] # [0, 1, 2]

  Example 2 (throws an exception only when 'await' is called):
  @async()
  def test():
    raise Exception()
  thread = test()
  thread.await() # Exception is not raised until this line
  """

  assert type(thread_pool_size) is int and thread_pool_size >= 1
  semaphore = Semaphore(thread_pool_size)
  def decorator(f):
    @wraps(f)
    def run(*args, **kwargs):
      
      class AwaitThread(Thread):

        def run(self):
          semaphore.acquire()
          try:
            self.result = f(*args, **kwargs)
          except Exception as e:
            self.exception = e
          finally:
            semaphore.release()

        def await(self):
          self.join()
          try:
            return self.result
          except:
            raise self.exception from None

      thread = AwaitThread()
      thread.start()
      return thread
    return run
  return decorator
