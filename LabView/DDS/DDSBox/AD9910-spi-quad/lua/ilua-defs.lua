ilua.line_handler(function (line)
    if line:sub(1,1) == '.' then -- a shell command!
        os.execute(line:sub(2))
        return nil
    else
        return line
    end
end)