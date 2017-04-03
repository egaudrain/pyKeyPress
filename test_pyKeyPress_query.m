
q = struct();
%q.from = GetSecs()-10;
%q.first = 1;
q.shutdown = true;

resp = pyKeyPress_query(q);