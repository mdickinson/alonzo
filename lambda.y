%token ID

%%

expr: atom | expr atom;
names: ID | names ID;
atom: ID | '(' expr ')' | '\\' names '.' expr;
