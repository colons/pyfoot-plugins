def send(irc, target, message):
    """ Raw version of IRC.send """
    try:
        if 'c' in irc.channels[target]['modes']:
            message = irc.strip_formatting(message)
    except KeyError:
        pass

    message = 'PRIVMSG %s :%s\r\n' % (target, message)
    print(' >> %s' % message)

    irc.socket.send(message)
