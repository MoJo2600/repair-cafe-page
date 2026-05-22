import requests, inspect, json, time, pytz

class lokilog:
    def __init__(self, https_url, host, source, env, version, enabled=True):
        self.url = https_url
        self.source = source
        self.host = host
        self.session = requests.Session()
        self.env = env
        self.version = version
        self.enabled = enabled

    def __send(self, lvl, payload):
        if not self.enabled:
            return "Logging is disabled"
        else:
            # JSON message
            func = self.__getCallstack(inspect.getouterframes(inspect.currentframe()))
            data = {
                        "streams": [
                            {
                                "stream": {
                                    'source': self.source,
                                    'job': func,
                                    'host': self.host,
                                    'level': lvl,
                                    'envconfig': self.env,
                                    'version': self.version
                                },
                                "values": [
                                    [
                                        str(time.time_ns()), json.dumps(payload)
                                    ]
                                ]
                            }
                        ]
                    }
            r = self.session.post(self.url, data=json.dumps(data), headers={"Content-Type": "application/json"})
            return json.dumps(data), r.status_code, r.text
    
    def __getCallstack(self, frameStack):
        callstack = []
        for index in range(2 if len(frameStack)>=4 else len(frameStack)-2):
            callstack.append(frameStack[index+2].function) if index+2 <= len(frameStack) and index<=6 else ""
        return ",".join(callstack)

    def info(self, jsonMsg):
        return self.__send("INFO", jsonMsg)

    def debug(self, jsonMsg):
        return self.__send("DEBUG", jsonMsg)

    def warn(self, jsonMsg):
        return self.__send("WARNING", jsonMsg)

    def error(self, jsonMsg):
        return self.__send("ERROR", jsonMsg)