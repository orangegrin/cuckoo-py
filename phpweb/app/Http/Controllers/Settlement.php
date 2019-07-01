<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use DB;
class Settlement extends Controller
{
    public function index()
    {
        // $users = [
        //     '0' => [
        //         'first_name' => 'Renato',
        //         'last_name' => 'Hysa'
        //     ],
        //     '1' => [
        //         'first_name' => 'Jessica',
        //         'last_name' => 'Alba'
        //     ]
        // ];
        // return $users;

        $data = DB::select('select * from settlement order by id desc limit 1440');
        // $ret_data = [];
        // foreach($data as $d)
        // {
        //     $ret_data[] = [
        //         'create_time'=> date('Y-m-d H:i:s',$d->create_time),
        //         'final_bal'=>$d->final_bal,
        //         'win_amount'=>$d->win_amount,
        //         'win_rate'=>$d->win_rate
        //     ];
        // }
        // return view('admin.users.index', compact('users'));
        return view('settlement.index',compact('data'));
        // return $ret_data;
    }
}
