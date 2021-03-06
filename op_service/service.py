import flask
import inspect
import json
import logging

from collections import defaultdict, Iterable
from datetime import datetime
from flask_cors import CORS
from functools import wraps

# This import configures the logging appropriately
print("\n\nABOUT TO DO THE IMPORT...\n\n")
from . import logging_config


class NotFound(Exception):
  pass


class BadRequest(Exception):
  pass


class AuthorizationException(Exception):
  pass


class ConflictException(Exception):
  pass


class InvalidAuthorizationHeader(AuthorizationException):
  pass


class InvalidTokenSignature(AuthorizationException):
  pass


class ExpiredTokenSignature(AuthorizationException):
  pass


class MissingRequiredClaim(AuthorizationException):
  pass


class InvalidAuth0Client(AuthorizationException):
  pass


class InvalidSubject(AuthorizationException):
  pass


# Converts datetimes to ISO formatted strings
# Converts unserializable iterables to lists
class _APIOutputJSONEncoder(json.JSONEncoder):

  def default(self, obj):
    if isinstance(obj, datetime):
      return obj.isoformat()
    try:
      return json.JSONEncoder.default(self, obj)
    except TypeError:
      if isinstance(obj, Iterable):
        return [i for i in obj]
      raise


DEFAULT_CONFIG_FILE_PATH = "run/config.json"
def _load_config(override_config_file_path):
  config_file_path = override_config_file_path or DEFAULT_CONFIG_FILE_PATH
  try:
    config_file = open(config_file_path)
    logging.info("Loading config from file at path '%s'..." % config_file_path)
    serialized_config = config_file.read()
    config = json.loads(serialized_config)
    logging.info("Successfully loaded config")
  except FileNotFoundError as e:
    if override_config_file_path:
      # If we've manually specified a particular config file, enforce that it actually exists
      raise Exception("No config file found at path '%s'" % config_file_path) from e
    logging.info("No config file at default path '%s' (continuing with empty config)" % config_file_path)
    config = {}
  return config


class OPService(object):

  def __init__(self, config_file_path=None):
    self.config = _load_config(config_file_path)

    self.flask_app = flask.Flask('op-service')
    CORS(self.flask_app)

    self.apis = []

    # Every service has a "health" endpoint (used by Elastic Beanstalk)
    @self.flask_app.route("/health", methods=['GET'])
    def health():
      return ""

    # Every service has an "explore" endpoint
    # TODO: consider adding authentication here
    @self.flask_app.route("/explore", methods=['POST'])
    def explore():
      grouped_apis = defaultdict(list)
      for api in self.apis:
        grouped_apis[api['grouping']].append(api)
      output = []
      for key in sorted(grouped_apis):
        output.append({
          'group': key,
          'apis': [
            {
              'endpoint': i['endpoint'],
              'input': describe(i['input_format']),
              'documentation': i['documentation']
            } for i in grouped_apis[key]
          ]
        })
      return self._make_json_response(output)

    # Anything declared in this map (of error_type -> error_code) will get converted to a neatly formatted JSON
    #   exception
    ERROR_HANDLERS = {
      BadRequest: 400,
      AuthorizationException: 401,
      NotFound: 404,
      ConflictException: 409,

      # Override the default error pages when Flask generates these error codes
      404: 404,
      500: 500
    }

    for key, value in ERROR_HANDLERS.items():
      @self.flask_app.errorhandler(key)
      def handle_bad_request(error):
        return self._prepare_error_response(error, value)

  def _make_json_response(self, output):
    serialized_output = json.dumps(output, cls=_APIOutputJSONEncoder)
    response = self.flask_app.make_response(serialized_output)
    response.mimetype = 'application/json'
    return response

  def _prepare_error_response(self, error, status_code):
    output = {
      'error_code': error.__class__.__name__,
      'error_message': str(error)
    }
    response = self._make_json_response(output)
    response.status_code = status_code
    return response

  def start(self, host='0.0.0.0', port=5000):
    self.flask_app.run(host=host, port=port, threaded=True)

  def api(self, endpoint, input_format=None, requires_auth=None):
    def decorator(f):
      calling_module = inspect.getmodule(inspect.currentframe().f_back)
      calling_module_name = calling_module and calling_module.__name__ or None
      self.apis.append({
        'endpoint': endpoint,
        'input_format': input_format or None,
        'grouping': calling_module_name,
        'documentation': f.__doc__
      })

      @self.flask_app.route(endpoint, methods=['POST'])
      @wraps(f)
      def run():
        if not flask.has_app_context():
          raise Exception('No request context (do not call APIs directly)')

        # We do not need to do anything if this is the OPTIONS part of a CORS request
        # TODO: may want to think of a better way of doing this where we don't need to ignore all OPTIONS requests
        # - check if there is an x-request-id header, or potentially
        # https://docs.newrelic.com/docs/apm/transactions/cross-application-traces/cross-application-tracing
        if flask.request.environ['REQUEST_METHOD'] == 'OPTIONS':
          return

        if requires_auth:
          # Check for the Authorization: Bearer <token> header with the JWT
          # Make sure that this JWT has been issues by someone we trust
          pass

        input_data = None
        if input_format is not None:
          try:
            input_data = flask.request.get_json()
          except Exception:
            raise BadRequest('Error parsing JSON')

          # Throws a BadRequest if the input is not valid
          validate(input_data, input_format)

        output = f(flask.request.headers, input_data)

        return self._make_json_response(output)
      return run
    return decorator


# Returns a JSON dictionary that describes the input format by using function names
def describe(input_format):
  if type(input_format) is dict:
    output = {}
    for key in input_format:
      output[key] = describe(input_format[key])
    return output
  if type(input_format) is list:
    output = []
    for i in input_format:
      output.append(describe(i))
    return output
  return input_format is not None and input_format.__name__ or None


# Throws a BadRequest exception is there is a problem with the input
def validate(input_data, input_format, key=None):
  if not input_format:
    return
  try:
    if type(input_format) is dict:
      assert type(input_data) is dict, "Expected dictionary"
      for key in input_format:
        if len(key) > 2 and key[0] == '[' and key[-1] == ']':
          optional_key = key[1:-1]
          if optional_key in input_data:
            input_data[optional_key] = validate(input_data[optional_key], input_format[key], key=optional_key)
        else:
          input_data[key] = validate(input_data[key], input_format[key], key=key)
    elif type(input_format) is list:
      assert type(input_data) is list, "Expected list"
      for i in range(len(input_data)):
        input_data[i] = validate(input_data[i], input_format[0], key=("%s[%i]" % (key or "", i)))
    else:
      return input_format(input_data)
  except Exception as e:
    msg = e.__class__.__name__ + " " + str(e)
    if (key):
      msg = "Validation error on key '" + key + "': " + msg
    raise BadRequest(msg)
