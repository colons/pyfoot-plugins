def send(irc, target, message):
    """ Raw version of IRC.send """
    try:
        if 'c' in irc.channels[target]['modes']:
            message = irc.strip_formatting(message)
    except KeyError:
        pass

    message = b'PRIVMSG ' + target + b' :' + message + b'\r\n'
    print(' >> %s' % message)

    irc.socket.send(message)
