import logging
import autonetkit.log as log


class AnkElement(object):

    # TODO: put this into parent __init__?
    def init_logging(self, my_type):
        return
        try:
            self_id = str(self)
        except Exception, e:
            # TODO: log warning here
            import autonetkit.log as log
            log.warning("Unable to set per-element logger %s", e)
            self_id = ""

        log_extra = {"type": my_type, "id": self_id}
        object.__setattr__(self, 'log_extra', log_extra)

    def log_info(self, message):
        log.info(message, extra=self.log_extra)

    def log_warning(self, message):
        log.warning(message, extra=self.log_extra)

    def log_error(self, message):
        log.error(message, extra=self.log_extra)

    def log_critical(self, message):
        log.critical(message, extra=self.log_extra)

    def log_exception(self, message):
        log.exception(message, extra=self.log_extra)

    def log_debug(self, message):
        log.debug(message, extra=self.log_extra)
