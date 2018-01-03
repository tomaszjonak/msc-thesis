% sygnal po kompresji tzw. bitstream zapisywany jest w katalogu "bs"
% sygnal zrekonstruowany zapisywany jest w katalogu "rec"
% uzyskany stopien kompresji oraz blad w katalogu "res"
% Wymagania: Matlab R2009, Wavelet_Toolbox441, Signal_Processing_Toolbox612

% d_path - sciezka do danych do kompresji

%% funkcja do testowania kompresji/dekompresji przykladowych danych
function lp_coder_test()

%% wybierz mod pracy 
lp_mode = 'test'; % kompresja i dekompresja
% lp_mode = 'enc';  % kompresja
% lp_mode = 'dec';   % dekompresja

%% sciezka do danych
% d_path = './dane_1f';     n_sig = 4; %syganly "o jednej cz", 4-sygna³y
d_path = './dane_2f';   n_sig = 6;      %sygnaly "2f" 6-sygna³ów

%% parametry kompresji
q = 1;      % q >= 1
%wname = 'bior2.2';                      %<-- wybor transformaty
wname = 'sym4';                        %<-- wybor transformaty

%% nie ruszac
    param.k_z = 0; 
    param.k_v = 0;
    param.ESC_Q = 8;
    param.ESC_Z = 6;
    param.ESC_V = -1;
    param.k_max = 3;
    param.N0 = 2;
    param.A_MAX = 512;
    param.a_enc = 'vli';
    %param.a_enc = 'agre';

    
    switch(lp_mode)
    case {'test'}
        lp_enc(d_path, wname, q, param);
        lp_dec(d_path, wname, q, param, n_sig);
    case {'enc'}
        lp_enc(d_path, wname, q, param);
    case {'dec'}
        lp_dec(d_path, wname, q, param, n_sig);
    end
return    
    

function lp_enc(d_path, wname, q, param)
    file_lst = dir([d_path, '/*.lvm']);
    lista_plikow_len = length(file_lst);
    
    n_levels = 6;
    dwtmode('per', 'nodisp');
    ka = 0; kd = zeros(1,n_levels);

    k = [];
    for f=1:lista_plikow_len
        fname = file_lst(f).name;
        d = load([d_path, '/', fname]);
        n_sig = size(d, 2)-1;
        
        dot = strfind(fname, '.');
        fname = fname(1:dot(end)-1);
        d2 = [];
        
        for s=1:n_sig
            x = d(:,1+s)';
        
            N = length(x);
            [xa, xd] = fdwt(x, wname, n_levels);
            [xa, xd, nz] = q_dwt(xa, xd, q);
                
            [bs, ka, kd] = enc_v3(xa, xd, param);
            bps = length(bs)/length(x);
%             k = [k; [ka, kd]];
            
            bs_name = ['bs/',fname, '_', wname, '_', num2str(s)];
            bs_write(bs, N, bs_name);
            disp(sprintf('ENC: %s, signal:%d, bps=%.3f', fname, s, bps));
        end
    end
return

    
function lp_dec(d_path, wname, q, param, n_sig)
    file_lst = dir([d_path, '/*.lvm']);
    lista_plikow_len = length(file_lst);
    
    n_levels = 6;
    dwtmode('per', 'nodisp');
    ka = 0; kd = zeros(1,n_levels);
    

    chk_err = 1;  %wykonaj porownanie z oryginalem
    fp_res = fopen(['res/' wname, '.txt'], 'w');
    
    for f=1:lista_plikow_len
        fname = file_lst(f).name;
        if(chk_err)
            d = load([d_path, '/', fname]);
        end
        
        dot = strfind(fname, '.');
        fname = fname(1:dot(end)-1);
        d2 = [];
        
        for s=1:n_sig
            bs_name = ['bs/',fname, '_', wname, '_', num2str(s)];
            [N, bs] = bs_read(bs_name);
            disp(sprintf('DEC: %s', bs_name));
        
            [xa2, xd2] = dec_v3(bs, n_levels, N, ka, kd, param);
%             chk_dec(xa, xd, xa2, xd2);

            x2 = iwt(xa2, xd2, wname, N);
            d2(:, s+1) = x2;

            n = 1:N;
            if(chk_err)
                x = d(:,1+s)';
                bps = length(bs)/length(x);
                e = sqrt(mean((x2-x).^2))/max(abs(x))*100;
                plot(n, x, 'r', n, x2, 'g');
                title(sprintf('e=%.2f, bps=%.2f', e, bps));
        
                fprintf(fp_res, 'e=%.2f, bps=%.2f, %s_%d\n', e, bps, fname, s);
                %pause
            else
                plot(n, x2, 'g');
                pause
            end
        end
        fs = 10000;
        d2(:, 1) = [0:length(x2)-1]/fs;
        save(['rec/', fname, '.lvm'], 'd2', '-ascii');
    end
return        



function chk_dec(xa, xd, xa2, xd2)
    e = sum(abs(xa - xa2));
    if(e>0) 
        error('chk_dec xa');
    end
        
    N = length(xd);
    for n=1:N
        e = sum(abs(xd{n} - xd2{n}));
        if(e>0) 
            error('chk_dec xd');
        end
    end
return


function bs_write(bs, N, fname)
    N_bs = dec2bin(N, 14);
    N = length(bs)+14;
    bz = repmat('0', 1, ceil(N/8)*8-N);
    bs = [N_bs, bs, bz];
    N = length(bs);
    fp = fopen([fname, '.bs'], 'w');
    for n=1:8:N
        b = bin2dec(bs(n+[0:7]));
        fwrite(fp, b, 'uint8');
    end
    fclose(fp);
return


function [N, bs] = bs_read(fname)
    fp = fopen([fname, '.bs'], 'r');
    x = fread(fp, 1000, 'uint8');
    N = length(x);
    bs = '';
    bs(N*8)='0';
    for n=0:N-1
        bs(n*8+[1:8]) = dec2bin(x(1+n), 8);
    end
    N = bin2dec(bs(1:14));
    bs = bs(15:end);
return



function [bs, ka, kd] = enc_v3(xa, xd, param)
    k_max = param.k_max ;
    N0    = param.N0;
    A_MAX = param.A_MAX;

    kod = zeros(10000, 5); p = 1;  %[type nz, k, cw, cn]

    L = length(xd);
    v = zeros(1, 1+sum(2.^[0:L-1]));
    
    ka = k_opt(xa);
    for n=1:L
        kd(n) = k_opt(xd{n});
    end
    
    N = 0; A = 0; 
    len_xa = length(xa); 
    
    p = 1;
    for k=0:len_xa-1
        v(1) = xa(1+k);
        d = 1;
        for n=L:-1:1
            v(1+d+[0:d-1]) = xd{n}(1+d*k+[0:d-1]);
            d = d*2;
        end
        
        if(k_max)
            ka = k_get(N, A, k_max);
            [N,A] = NA(N,A, v(1), N0, A_MAX);
        end
        [kod, p] = enc_vect(v, kod, p, ka, kd, param);
    end 
    kod = kod(1:p-1,:);
    kod_len = sum(kod(:,5));
    
    nz_i = kod(:, 1)==0;
    nz_len = sum(kod(:, 5).*nz_i);
    v_i = kod(:,1)==1;
    v_len = sum(kod(:, 5).*v_i);
        
    bs = cw2bs(kod(:,4), kod(:,5));
return


function k = k_get(N, A, k_max)
    k = sum(2.^[0:k_max] * N <= A);
return    

function [N,A] = NA(N, A, v, N0, A_MAX)
    if(N0==1)
        N=1;
        A=abs(v);
        return;
    end
    N=N+1;
    A=A+abs(v);

    if(A>A_MAX)
		A=A_MAX;
	end
    
    if(N==N0)
        N = fix(N/2);
        A = fix(A/2);
    end
return



function k_min = k_opt(x)
    ESC_Q = 8;
    nz = x(x~=0);
    N = length(nz);
    cn_min = N*16;
    k_min = 0;
    if(N==0)
        return;
    end
    
    for k=0:3
        CN = 0;
        for n=1:N
            u = nz(n);
            v = gmap1(u);
            [cw, cn] = GR0(v, k, ESC_Q, 6); 
            CN = CN + cn;
        end
        if(CN < cn_min)
            cn_min = CN;
            k_min = k;
        end
    end
return


function [kod, p] = enc_vect(V, kod, p, ka, kd, param)
    L = length(V);
    p0 = p;
    
    k_z = param.k_z; 
    k_v = param.k_v;
    ESC_Q = param.ESC_Q ;
    ESC_Z = param.ESC_Z ;
    ESC_V = param.ESC_V ;
    
    
    if(sum(V==0)==L)
        kod(p, :) = [1, 0, k_z, 0, 1];  %EOB: cw = 0, cn = 1; 
        p = p + 1;
        return;
    end
    
    nz = 0;
    for n=1:L
        u = V(n);
        if(u==0)
            nz = nz + 1;
            continue;
        end
        nz = nz + 1;
        [cw, cn] = GR0(nz, k_z, ESC_Q, ESC_Z);
        %if(nz>=32)
        %    nz
        %end
        kod(p, :) = [0, nz, k_z, cw, cn];
        p = p + 1;
        k_v = 0;
        nz = 0;
        v = gmap1(u);
        
        if(n==1)
            switch(param.a_enc)
            case {'vli'}
                bits = 1+floor(log2(abs(u)));
                v = u;
                if(u<0)
                    v = abs(u)-2^(bits-1);
                end
                cw = bits*2^(bits) + v;  cn = 4+bits;
            case {'gre', 'agre'}
                [cw, cn] = GR0(v, ka, ESC_Q, ESC_V);
            end
        else
            [cw, cn] = GR0(v, k_v, ESC_Q, ESC_V);
        end
        kod(p, :) = [1, u, k_v, cw, cn];
        p = p + 1;
    end
    
    if(n==L && u==0) %EOB
        kod(p, :) = [0, 0, 0, 0, 1];
        p = p + 1;
    end
    
    kod_len = sum(kod(p0:p-1, 5));
return



function [V, p] = dec_vect(bs, p, N, ka, kd, param)
    ESC_Q = param.ESC_Q ;
    ESC_Z = param.ESC_Z ;
    ESC_V = param.ESC_V ;
    k_v = param.k_v;
    
    V = zeros(1, N);
    
    n = 0;
    while(n < N)
        [nz, p] = dGR0(bs, p, 0, ESC_Q, ESC_Z);
        if(nz==0) %EOB
            return;
        end
        n = n + nz;
        
        if(n==1)
            switch(param.a_enc)
            case {'vli'}
                bits = bin2dec( bs(p:p+4-1) ); p = p + 4;
                u = 0;
                if(bits)
                    u = bin2dec( bs(p:p+bits-1) ); p = p + bits;
                end
                if(u < 2^(bits-1))
                    u = -(u + 2^(bits-1));
                end
            case {'gre', 'agre'}
                [v, p] = dGR0(bs, p, ka, ESC_Q, ESC_V);
                u = gdmap1(v);
            end
        else
            [v, p] = dGR0(bs, p, k_v, ESC_Q, ESC_V);
            u = gdmap1(v);
        end
        V(n) = u;
    end
return



function [xa, xd] = dec_v3(bs, n_levels, Nx, ka, kd, param)
    k_max = param.k_max ;
    N0    = param.N0;
    A_MAX = param.A_MAX;
    
    len_xa = ceil(Nx/2^n_levels);
    
    LenA = len_xa;
    
    xa = zeros(1, LenA);
    for i=n_levels:-1:1
        xd{i} = zeros(1, LenA);
        LenA = 2*LenA;
    end
    
    N = 0; A = 0; 
    
    VN = 1+sum(2.^[0:n_levels-1]);
    k = 0;
    p = 1; bs_len = length(bs);
    
    for k=0:len_xa-1
        if(k_max)
            ka = k_get(N, A, k_max);
        end
        [v, p] = dec_vect(bs, p, VN, ka, kd, param);
        if(k_max)
            [N,A] = NA(N,A, v(1), N0, A_MAX);
        end
        xa(1+k) = v(1);
        d = 1;
        for n=n_levels:-1:1
            xd{n}(1+d*k+[0:d-1]) = v(1+d+[0:d-1]);
            d = d*2;
        end
    end
    
return








function [c, n] = GR0(v, k, ESC_Q, ESC_B)
    k = max(k,0);
    q = floor(v/2^k);          r = rem(v, 2^k);
    
    c = 0;
    if(q < ESC_Q)
        %c_ref = bin2dec([dec2bin(r, k), '0', repmat('1', 1, q)]);
        c = (2^q-1)*2^(1+k) + r;
        %if(c_ref ~= c) error('GR0: c_ref ~= c'); end
        n = q+1 + k;
    else
        if(ESC_B==-1)
            msb = floor(log2(v));
            u  = v - 2^msb;			% clear MSB, MSB always == 1 
            %c = (u << 8+3) + ((msb-3) << 8) + (1 << 8)-1
            c = (2^ESC_Q-1)*2^(msb+3) + (msb-3)*2^(msb) + u;
            n = msb + 3 + 8;
        else
            c = (2^ESC_Q-1)*2^ESC_B + v;
            n = ESC_Q + ESC_B;
        end
    end
return

function [x, p] = dGR0(bs, p, k, ESC_Q, ESC_B)
    if(nargin==1)
        k=0;
    end
    %p=1;
    n=0;
    while(bs(p)=='1')
        n=n+1;
        p=p+1;
        if(n==ESC_Q)
            if(ESC_B==-1)
                msb = bin2dec( bs(p:p+3-1) ) + 3; p = p + 3;
                u = bin2dec( bs(p:p+msb-1) ); p = p + msb;
                x = u + 2^msb;
            else
                x = bin2dec( bs(p:p+ESC_B-1) );
                p = p + ESC_B;
            end
            return;
        end
    end
    
    p=p+1;
    r=0;
    if(k)
        r = bin2dec( bs(p:p+k-1) );
    end
    p = p+k;
    %kod = kod(p+k:end);
    x = n*2^k + r;
return


function x=gdmap1(z)
    if(rem(z,2))
        x = (z+1)/2;
    else
        x = -(z/2+1);
    end
return




function bs = cw2bs(cw, cn)
    bs = zeros(1, sum(cn));
    L = length(cn);
    p = 0;
    for k=1:L
        bs(p+[1:cn(k)]) = dec2bin(cw(k), cn(k));
        p = p + cn(k);
    end
    bs = sprintf('%c',bs);
return



function [xa, xd, nz] = q_dwt(xa, xd, q)
    N = length(xd);
    e = sum(xa.^2);
    for n=1:N
        e = e + sum(xd{n}.^2);
    end
    
    xa = round(xa/q)*q;
    nz = sum(xa~=0);
    for n=1:N
        xd{n} = round(xd{n}/q)*q;
        nz = nz + sum(xd{n}~=0);
    end
return


function [xa, xd] = fdwt(x, wname, n_levels)
    N = length(x);
    xd = {};
    x = [x, zeros(1, ceil(N/2^n_levels)*2^n_levels-N)];
        
    for n=1:n_levels
        [xa, xd{n}] = dwt(x, wname);
        %[Lo_D, Hi_D, Lo_R, Hi_R] = wfilters(wname);
        x = xa;
    end
return


function x = iwt(xa, xd, wname, N)
    x = xa;
    n_levels = length(xd);
    for n=n_levels:-1:1
        x = idwt(x, xd{n}, wname);
    end
    x = x(1:N);
return


function z=gmap1(x)
    if(x>0)
        z=2*x-1;
    elseif(x<0)
        z=2*(abs(x)-1);
    else
        z=[];
    end
return



