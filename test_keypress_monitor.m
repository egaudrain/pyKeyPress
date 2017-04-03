
% 1. Start the monitor
% In a console:
% python cocoa_keypress_monitor.py
%
% From this point on do not use the keyboard anymore.
%
% Return here, place the cursor at the end of this line and press Run
% with the mouse. Place cursor here: 
%

% 2. Create a robot for virtual keypress
import java.awt.*;
import java.awt.event.*;

rob=Robot;

tm = [];
tm_after = [];
%cm = {};

tic();

N = 100;
for i=1:N
    tm = [tm, toc()];
    rob.keyPress(KeyEvent.VK_A);
    tm_after = [tm_after, toc()];
    pause(.1);
end

rob.keyPress(KeyEvent.VK_E); pause(.1);
rob.keyPress(KeyEvent.VK_X); pause(.1);
rob.keyPress(KeyEvent.VK_I); pause(.1);
rob.keyPress(KeyEvent.VK_T); pause(.1);
rob.keyPress(KeyEvent.VK_M); pause(.1);
rob.keyPress(KeyEvent.VK_O); pause(.1);
rob.keyPress(KeyEvent.VK_N); pause(.1);
rob.keyPress(KeyEvent.VK_I); pause(.1);
rob.keyPress(KeyEvent.VK_T); pause(.1);
rob.keyPress(KeyEvent.VK_O); pause(.1);
rob.keyPress(KeyEvent.VK_R);

pause(.5);
log()

t = t(1:N);
%c = c{1:end-10};

tmm = (tm+tm_after)/2;

figure(1)
plot(tmm-tmm(1), t-t(1), '+');

figure(2)
hist((tmm - tmm(1)) - (t - t(1)))

std((tmm - tmm(1)) - (t - t(1)))



