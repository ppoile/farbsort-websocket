import datetime
import logging
import Queue
import time


def setup_logging(verbose=False):
  logging_level = logging.INFO
  if verbose:
    logging_level = logging.DEBUG
  logging.basicConfig(level=logging_level)

setup_logging()


class Controller(object):
  def __init__(self, hal, pru):
    self._logger = logging.getLogger(self.__class__.__name__)
    self._logger.debug("init")
    self._hal = hal
    self._pru = pru
    self._motor_running = False
    self._listener = None
    self._hal.register_on_input_change_callback(self._on_input_change)
    self._connected = False

  def register_event_listener(self, listener):
    self._listener = listener

  def connect(self):
    self._connected = True
    self.post_event("conveyor={}".format("running" if self.motor else "stopped"))
    self.post_event("compressor={}".format("start" if self.compressor else "stop"))
    self.post_event("lightbarrier3={}".format("on" if self.lightbarrier3 else "off"))
    self.post_event("lightbarrier4={}".format("on" if self.lightbarrier4 else "off"))
    self.post_event("lightbarrier5={}".format("on" if self.lightbarrier5 else "off"))
    #self._pru.write(chr(1))

  def disconnect(self):
    self._pru.write(chr(2))
    self._connected = False

  def post_event(self, msg):
    if self._connected and self._listener:
      self._listener.on_event_received(msg)

  def on_poll(self):
    self._hal.get_input(self._hal.LIGHTBARRIER3)
    self._hal.get_input(self._hal.LIGHTBARRIER4)
    self._hal.get_input(self._hal.LIGHTBARRIER5)

    event = self._pru.read()
    if event != "":
      self._logger.debug("Got {}".format(repr(event)))
      self.post_event(event)

  def on_stdin(self, fd, events):
    raw_line = fd.readline()
    self._logger.debug("stdin: Got {}".format(repr(raw_line)))
    command = raw_line.strip()
    if command != "":
      self.post_event(command)

  @property
  def motor(self):
    return self._motor_running

  @motor.setter
  def motor(self, value):
    self._motor_running = value
    self._pru.write(b'\x09' if value else b'\x0a')
    self.post_event("conveyor={}".format("running" if value else "stopped"))
    # return retval

  @property
  def compressor(self):
    return self._hal.get_output(self._hal.COMPRESSOR)

  @compressor.setter
  def compressor(self, value):
    retval = self._hal.set_output(self._hal.COMPRESSOR, value)
    self.post_event("compressor={}".format("start" if value else "stop"))
    return retval

  @property
  def lightbarrier3(self):
    return self._hal.get_input(self._hal.LIGHTBARRIER3)

  @property
  def lightbarrier4(self):
    return self._hal.get_input(self._hal.LIGHTBARRIER4)

  @property
  def lightbarrier5(self):
    return self._hal.get_input(self._hal.LIGHTBARRIER5)

  def _on_input_change(self, pin, value, last_value):
    now = datetime.datetime.now()
    display_value = "on" if value else "off"
    self.post_event("{}={}".format(pin, display_value))
    self._logger.debug("pin {} changed: {} -> {}".format(
      pin, "on" if last_value else "off", display_value))

  @staticmethod
  def split_command_into_key_and_value(command):
    value = ""
    fields = command.split("=", 1)
    key = fields[0]
    if len(fields) > 1:
      value = fields[1]
    return key, value

  def dispatch_command(self, command):
    print "command received"
    print command
    key, value = self.split_command_into_key_and_value(command)
    if key == "start":
      self._pru.write(b'\x07')
    elif key == "stop":
      self._pru.write(b'\x08')
    elif key == "mode":
      if value == "normal":
        self._pru.write(b'\x05')
      else:
        self._pru.write(b'\x06')
    elif key == "motor":
        self.motor = value in ("on", "start")
    elif key == "valve1":
      if value == "on":
        self._pru.write(b'\x0b')
      else:
        self._pru.write(b'\x0c')
    elif key == "valve2":
      if value == "on":
        self._pru.write(b'\x0d')
      else:
        self._pru.write(b'\x0e')
    elif key == "valve3":
      if value == "on":
        self._pru.write(b'\x0f')
      else:
        self._pru.write(b'\x10')
    elif key == "compressor":
      self.compressor = value in ("on", "start")


  def __del__(self):
    self._logger.debug("delete")
    self.motor = False
    self.compressor = False
    self.valve1 = False
    self.valve2 = False
    self.valve3 = False


if __name__ == "__main__":
  import time

  from hal import HAL
  from pru import PRU

  hal = HAL()
  pru = PRU()
  controller = Controller(hal, pru)

  class EventListener(object):
    def __init__(self):
      self.events = []

    def on_event_received(self, event):
      print "event: {}".format(repr(event))

  event_listener = EventListener()
  controller.register_event_listener(event_listener)
  controller.on_poll()
  controller.connect()
  controller.on_poll()
  controller.compressor = True
  time.sleep(2)
  controller._pru.write(chr(7))

  try:
    while True:
      controller.on_poll()
      time.sleep(.001)
  except KeyboardInterrupt:
    print "\nTerminating..."
  finally:
    controller._pru.write(chr(8))
    controller.on_poll()
    time.sleep(2)
    controller.on_poll()
    controller.compressor = False
    controller._pru.write(chr(2))
    controller.on_poll()
