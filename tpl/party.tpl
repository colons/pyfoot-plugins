%rebase tpl/base title='party', network=network
<p class="summary"><a href="/help/{{network}}/">help</a> | <a href="..">additional parties</a></p>

<div class="section party">
    <div class="heading">
        <h3>party</h3>
        <p>via {{party['via']}}</p>
    </div>
    <div class="key">
        <p class="irc">{{party['nick']}}</p>
        <p class="irc">{{party['source']}}</p>
    </div>
    <div class="item phrases">
    %for line in party['lines']:
        <p>{{line}}</p>
    %end
    </div>
</div>
