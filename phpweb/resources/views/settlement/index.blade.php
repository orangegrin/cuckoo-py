
<table border="1">
    <tr>
        <th>时间</th>
        <th>余额</th>
        <th>盈利</th>
        <th>比例</th>
    </tr>
    @foreach($data as $d)
        <tr>
            <td> {{ date('Y-m-d H:i:s',$d->create_time) }} </td>
            <td> {{ $d->final_bal }} </td>
            <td> {{ $d->win_amount }} </td>
            <td> {{ $d->win_rate }} </td>
        </tr>
    @endforeach
</table>