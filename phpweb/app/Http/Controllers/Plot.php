<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use DB;
class Plot extends Controller
{
    public function index(Request $request)
    {
        $exchange_a = $request->input('exchange_a');
        $exchange_b = $request->input('exchange_b');
        $symbol_a = $request->input('symbol_a');
        $symbol_b = $request->input('symbol_b');

        $end_time = time();
        $file_name = md5($exchange_a.$exchange_b.$symbol_a.$symbol_b.$end_time).'.html';
        
        $python_path = getenv('BPLOT_PYTHON_PATH');
        $python_file = $python_path.'/bqplot.py';
        $plot_file = $python_path."/plothtml/$file_name";

        // var_dump($python_path);
        $cmd = <<<EOT
        python3 $python_file --exchange_a=$exchange_a --exchange_b=$exchange_b --symbol_a=$symbol_a --symbol_b=$symbol_b --time_end=$end_time --file_name=$plot_file
EOT;
        // var_dump($cmd);
        $ret = \shell_exec($cmd);
        echo file_get_contents($plot_file);
        // var_dump($plot_file);
    }
}
