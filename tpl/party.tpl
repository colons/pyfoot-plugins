%rebase tpl/base title='party', network=network
<p class="summary"><a href="/help/{{network}}/">help</a> | <a href="..">additional parties</a></p>

<div class="section party">
    <div class="heading">
        <h3>party</h3>
        % if 'via' in party:
        <p>via {{party['via']}}</p>
        % end
    </div>
    <div class="key">
        % for key in ['nick', 'source']:
        % if key in party:
        <p class='irc'>{{party[key]}}</p>
        %end
        %end
    </div>
    <div class="item phrases">
    %for line in party['lines']:
        <p>{{line}}</p>
    %end
    </div>
</div>
