%rebase tpl/base title='parties', network=network
<p class="summary"><a href="/help/{{network}}/">help</a>

<div class="section">
    <div class="heading">
        <h3>parties</h3>
    </div>
    %for party in parties:
    <div class="key">
        <p class='irc'>{{party['nick']}}</p>
        <p class='irc'>{{party['source']}}</p>
    </div>
    <div class="item">
        <p>{{party['initial']}} <span class="separator">-&gt;</span> {{party['final']}}</p>
        <p><a href="{{party['url']}}">{{party['attempts']}} attempts</a></p>
    </div>
    %end
</div>
