from nicegui import ui, app
from datetime import datetime
import asyncio
import urllib.parse
import requests
import os


# --- SUPABASE CONFIGURATION ---
from supabase import create_client, Client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class MasterHubState:
    def __init__(self):
        self.is_logged_in = app.storage.user.get('logged_in', False)
        self.user_email = app.storage.user.get('email', '')
        self.current_screen = "main_hub" 
        self.current_screen = "dashboard"
        # --- AUTH & ROLE STATES ---
        self.email = ""
        self.user_email = ""
        self.is_logged_in = False
        self.otp_sent = False
        self.otp_timer = 0     
        self.user_role = None     
        self.account_status = "ACTIVE" 
        
        self.all_admins_list = []

        # --- 🏢 REPLACED MEENA ORIGINAL MATRIX ROUTING STATES ---
        self.selected_meena_tab = None        
        self.selected_room = None             
        self.room_sub_tab = None              
        self.available_rooms = []             
        
        # --- 📜 ORIGINAL MEENA WEBPAGE ENGINE STATE PROPERTIES ---
        self.member_view = "list"
        self.bill_type = "Electric"
        self.billing_tab = "current"
        self.rent_tab = "current"
        self.dynamic_family_members = []
        self.active_renter_head_id = None
        self.renter_id = None
        self.room_no = None
        
        # Room ke sabhi heads (Active + History) load karne ke liye dropdown state
        self.room_heads_options = []
        self.selected_head_option = None

        # 6 Tarik automatic current month decision core rule algorithm
        today = datetime.now()
        if today.day <= 5:
            prev_month_idx = today.month - 1 if today.month > 1 else 12
            calc_month = datetime(today.year, prev_month_idx, 1).strftime('%B')
        else:
            calc_month = today.strftime('%B')
        self.selected_month = calc_month
        self.history_month = calc_month
        
        

        # --- ⚙️ SETTINGS TOGGLE CONF ENGINE STATES ---
        self.electric_history_enabled = True
        self.gas_history_enabled = True

@ui.page('/')
def main_page():
    state = MasterHubState()

    # Refresh hone par session check karein
    if app.storage.user.get('logged_in'):
        state.is_logged_in = True
        state.user_email = app.storage.user.get('email', '')
        state.user_role = app.storage.user.get('role', 'admin')

    # 📱 FULL MOBILE/TABLET SCREEN CANVAS
    ui.query('body').style('background-color: #f1f8e9; margin: 0; padding: 0; width: 100vw; min-height: 100vh; overflow-x: hidden;')

    # HTML Head Configuration for PWA Links
    ui.add_head_html('<link rel="manifest" href="/static/manifest.json">')
    ui.add_head_html('<meta name="theme-color" content="#2e7d32">')
    ui.add_head_html( '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">')
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">')
    
    ui.add_head_html('''
    <style>
        .phone-wrapper {
            width: 100vw !important;       
            height: 100vh !important;      
            background-color: #f1f8e9 !important; 
            overflow: hidden !important;   
            position: relative;
            display: flex;
            flex-direction: column;
            margin: 0px !important;        
            padding: 0px !important;
        }
        .app-card {
            border-radius: 16px !important;
            border: 1px solid #c8e6c9 !important; 
            background: #ffffff !important;
            padding: 16px !important;
            transition: all 0.2s ease-in-out !important;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
            width: 100% !important;
        }
        .app-card:active {
            transform: scale(0.97) !important;
            background: #e8f5e9 !important; 
        }
        .nav-header-bar {
            background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%) !important;
            height: 56px;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            color: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.12);
        }
        .custom-drawer .q-drawer {
            background-color: #ffffff !important;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1) !important;
        }
        .meena-main-btn {
            width: 100%;
            height: 54px;
            font-size: 14px !important;
            font-weight: bold !important;
            border-radius: 14px !important;
        }
        .webpage-input {
            background-color: #ffffff !important;
            border-radius: 8px !important;
        }
        .tile-grid-container {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 12px !important;
            width: 100% !important;
        }
        .tile-card-btn {
            background: #ffffff !important;
            border: 2px solid #c8e6c9 !important;
            border-radius: 16px !important;
            padding: 16px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: all 0.15s ease-in-out !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
            height: 106px !important;
        }
        .tile-card-btn:active {
            transform: scale(0.96) !important;
            background: #e8f5e9 !important;
        }
        .blink-dot{
            width:10px;
            height:10px;
            border-radius:50%;
            background:red;
            animation:blink 1s infinite;
        }

        @keyframes blink{
            50%{opacity:0;}
        }
        .blink-dot-text{
            animation: blink 1s infinite;
        }
    </style>
    ''')

    # --- SUPABASE REALTIME ROOM FETCH ENGINE ---
    def fetch_realtime_rooms():
        try:
            res = supabase.table('renters').select('room_no').execute()
            if res.data:
                rooms = sorted(list(set([str(r['room_no']).strip() for r in res.data if r.get('room_no')])))
                state.available_rooms = rooms
            else:
                state.available_rooms = []
        except Exception as e:
            print(f"Room fetch error: {e}")
            state.available_rooms = []

    # DYNAMIC RENTER HEAD SELECTOR ENGINE (Active wale upar, Left wale neeche)
    def fetch_room_heads_history(room_no_val):
            try:
                renters = supabase.table(
                    'renters'
                ).select(
                    'id,status,head_member_id,created_at'
                ).eq(
                    'room_no', room_no_val
                ) .order('created_at',desc=True
                ).execute()
                options_list = []
                active_option = None
                for row in renters.data or []:
                    renter_id = row['id']
                    status = str(row.get('status', 'ACTIVE')).upper()
                    head_name = "Unknown Head"
                    head_id = row.get('head_member_id')
                    if head_id:
                        try:
                            h = supabase.table(
                                'public_members'
                            ).select(
                                'name'
                            ).eq(
                                'id', head_id
                            ).single().execute()

                            if h.data:
                                head_name = h.data.get('name', 'Unknown Head')
                        except Exception:
                            pass
                    
                    created_dt = ""
                    try:
                            raw_dt = row.get('created_at')

                            if raw_dt:
                                created_dt = datetime.fromisoformat(
                                    raw_dt.replace('Z', '+00:00')
                                ).strftime('%d-%b-%Y')
                    except:
                            pass
                    opt = {
                        'value': renter_id,
                        'label': f'{head_name} ({status}) - {created_dt}',
                        'status': status
                    }
                        
                    
                    options_list.append(opt)

                    if status == 'ACTIVE':
                        active_option = renter_id
                        

                state.room_heads_options = options_list

                if active_option:
                    state.selected_head_option = active_option
                elif options_list:
                    state.selected_head_option = options_list[0]['value']
                else:
                    state.selected_head_option = None

            except Exception as e:
                print("Head history error:", e)
        

    # --- OTP SECURITY AUTHENTICATION CONTROL ENGINE ---
    def handle_send_otp(email_val):
        if not email_val:
            ui.notify('Sahi email daalein', type='warning')
            return
        email_clean = str(email_val).strip().lower()
        if state.otp_sent and state.otp_timer > 0:
            ui.notify(f'Please wait {state.otp_timer}s', type='warning')
            return
            
        try:
            user_res = supabase.table('hub_users').select('*').eq('email', email_clean).execute()
            if not user_res.data:
                ui.notify('Access Denied: Email registry me nahi mila!', type='negative')
                return
                
            user_row = user_res.data[0]
            if user_row.get('status', 'ACTIVE') in ['BLOCKED', 'PAUSED']:
                ui.notify(f"Aapka account admin dwara {user_row.get('status')} kiya gaya hai!", type='negative')
                return
                
            supabase.auth.sign_in_with_otp({"email": email_clean})
            state.email = email_clean
            state.otp_sent = True
            state.otp_timer = 60
            ui.notify(f'OTP sent successfully!', type='positive')
            sidebar_content.refresh()
            main_container.refresh()
        except Exception as e:
            ui.notify(f'Error: {str(e)}', type='negative')

    def handle_verify_otp(otp_val):
        try:
            res = supabase.auth.verify_otp({"email": state.email, "token": otp_val.strip(), "type": "email"})
            if not res.user:
                ui.notify('Invalid OTP', type='negative')
                return
                
            state.user_email = state.email
            state.is_logged_in = True
            state.otp_sent = False
            state.otp_timer = 0
            state.current_screen = "main_hub"
            
            user_data = supabase.table('hub_users').select('*').eq('email', state.user_email).single().execute()
            if user_data.data:
                state.user_role = user_data.data.get('role', 'admin') 
                state.account_status = user_data.data.get('status', 'ACTIVE')
                
            ui.notify(f'Logged in as {str(state.user_role).upper()}', type='positive')
            sidebar_content.refresh()
            main_container.refresh()
        except Exception as e:
            ui.notify('Session expired ya Invalid OTP', type='negative')

        app.storage.user['logged_in'] = True
        app.storage.user['email'] = state.email
        state.is_logged_in = True


    def logout():
        app.storage.user.clear()
        state.is_logged_in = False
        state.otp_sent = False
        state.otp_timer = 0
        state.user_email = ""
        state.user_role = None
        state.current_screen = "main_hub"
        ui.notify('Logged out successfully')
        sidebar_content.refresh()
        main_container.refresh()

    def countdown_tick():
        if state.otp_timer > 0: 
            state.otp_timer -= 1
    ui.timer(1.0, countdown_tick)


    def share_bill_on_whatsapp(bill_exists, renter_id):
            import urllib.parse
            
            # 1. WhatsApp Number Fetch (public_members table se)
            whatsapp_no = "" 
            try:
                member_res = supabase.table('public_members').select('whatsapp').eq('renter_id', renter_id).eq('relation', 'Head').single().execute()
                if member_res.data and member_res.data.get('whatsapp'):
                    raw_number = str(member_res.data['whatsapp']).strip()
                    
                    # Agar number 10 digit ka hai, toh '91' prefix lagayein
                    if len(raw_number) == 10:
                        whatsapp_no = "91" + raw_number
                    # Agar pehle se country code hai (jaise 91XXXXXXXXXX), toh wahi rehne dein
                    else:
                        whatsapp_no = raw_number.replace('+', '') 
            except Exception as e:
                print("Error fetching number:", e)
            
            if not whatsapp_no:
                ui.notify("WhatsApp number nahi mila!", type='warning')
                return
            
            # 2. Message Formatting
            msg = f"""*🧾 Meena Residency Bill - {bill_exists.get('bill_month', 'N/A')}*
            
            *--- Bill Details ---*
            📅 Prev Date: {bill_exists.get('prev_reading_date', 'N/A')}
            📈 Prev Reading: {bill_exists.get('prev_reading', '0')} kWh
            
            📅 Curr Date: {bill_exists.get('curr_reading_date', 'N/A')}
            📈 Curr Reading: {bill_exists.get('curr_reading', '0')} kWh
            
            *--- Calculation ---*
            ⚡ Rate: ₹{bill_exists.get('rate_per_unit', '0')}
            ➕ Extra Units: {bill_exists.get('extra_units', '0')}
            🔋 Consumed Units: {bill_exists.get('total_consumed_units', '0')}
            
            *💰 Total Amount: ₹ {bill_exists.get('total_amount', '0')}*
            
            *🔗 View Image:* {bill_exists.get('bill_img_url', 'No Image') if bill_exists.get('bill_img_url') else 'N/A'}
            """
            
            # 3. WhatsApp URL Open
            encoded_msg = urllib.parse.quote(msg)
            ui.navigate.to(f"https://wa.me/{whatsapp_no}?text={encoded_msg}", new_tab=True)

    def share_current_rent_whatsapp(rent_row, renter_id):
            try:
                member = (
                    supabase.table('public_members')
                    .select('whatsapp')
                    .eq('renter_id', renter_id)
                    .eq('relation', 'Head')
                    .single()
                    .execute() )
                if not member.data:
                    ui.notify('WhatsApp number not found')
                    return
                whatsapp_no = str(member.data['whatsapp']).strip()
                if len(whatsapp_no) == 10:
                    whatsapp_no = "91" + whatsapp_no
                msg = f"""
        🏠 *RENT BILL*
        Month : {rent_row.get('bill_month')}
        Year : {rent_row.get('bill_year')}
        🏡 Flat Rent : ₹{rent_row.get('flat_bill',0)}
        ⚡ Electric : ₹{rent_row.get('electric_bill',0)}
        🔥 Gas : ₹{rent_row.get('gas_bill',0)}
        ➕ Extra : ₹{rent_row.get('other_charge',0)}
        💰 *Total Due : ₹{rent_row.get('total_charge',0)}*
        """
                encoded = urllib.parse.quote(msg)
                ui.navigate.to(
                    f"https://wa.me/{whatsapp_no}?text={encoded}",
                    new_tab=True)
            except Exception as e:
                ui.notify(str(e))
                print(e)
            
                
    def share_ledger_whatsapp(rows_data, overall_balance, renter_id):

                whatsapp_no = ""

                try:
                    member_res = supabase.table(
                        'public_members'
                    ).select(
                        'whatsapp'
                    ).eq(
                        'renter_id', renter_id
                    ).eq(
                        'relation', 'Head'
                    ).single().execute()

                    if member_res.data and member_res.data.get('whatsapp'):
                        raw = str(member_res.data['whatsapp']).strip()

                        if len(raw) == 10:
                            whatsapp_no = "91" + raw
                        else:
                            whatsapp_no = raw.replace('+', '')

                except Exception as e:
                    ui.notify("WhatsApp number nahi mila")
                    return

                msg = "*📊 BALANCE SHEET*\n\n"

                for r in rows_data:
                    msg += (
                        f"{r.get('bill_month')} {r.get('bill_year')}\n"
                        f"Due: ₹{r.get('total_charge',0)}\n"
                        f"Paid: ₹{r.get('deposite',0)}\n"
                        f"Balance: ₹{r.get('balance_amount',0)}\n\n"
                    )

                msg += f"💰 Overall Balance: ₹{overall_balance}"

                encoded = urllib.parse.quote(msg)

                ui.navigate.to(
                    f"https://wa.me/{whatsapp_no}?text={encoded}",
                    new_tab=True
                )
    def send_push(renter_id, title, body):
        try:
            res = (
                supabase.table('renters')
                .select('fcm_token')
                .eq('id', renter_id)
                .single()
                .execute())
            token = res.data.get('fcm_token')
            if not token:
                return
            requests.post(
                "https://fcm.googleapis.com/fcm/send",
                headers={
                    "Authorization": "key=YOUR_FIREBASE_SERVER_KEY",
                    "Content-Type": "application/json",},
                json={
                    "to": token,
                    "notification": {
                        "title": title,
                        "body": body } },timeout=5)
        except Exception as e:
            print("FCM Error:", e)
    # --- ☰ NATIVE SIDEBAR DRAWER ---
    with ui.left_drawer(value=False, fixed=True).classes('custom-drawer').props('side="left" width=260 behavior="mobile"') as sidebar:
        @ui.refreshable
        def sidebar_content():
            with ui.column().classes('w-full p-4 gap-4'):
                if not state.is_logged_in:
                    ui.label('Morya Hub Login').classes('text-xl font-black text-green-900 mt-2')
                    with ui.card().classes('w-full p-3 bg-slate-50 border shadow-none rounded-xl'):
                        with ui.column().bind_visibility_from(state, 'otp_sent', backward=lambda x: not x).classes('w-full'):
                            e_input = ui.input(label='Registered Email').classes('w-full').props('dense autofocus')
                            ui.button('Get OTP', on_click=lambda: handle_send_otp(e_input.value)).props('type=button').classes('w-full mt-2 bg-green-700 text-white font-bold rounded-lg')
                        with ui.column().bind_visibility_from(state, 'otp_sent').classes('w-full'):
                            ui.label().bind_text_from(state, 'email', backward=lambda x: f'OTP sent to {x}').classes('text-[10px] text-gray-500')
                            o_input = ui.input(label='Enter OTP').classes('w-full').props('dense autofocus')
                            ui.button('Verify OTP', on_click=lambda: handle_verify_otp(o_input.value)).props('type=button').classes('w-full mt-2 bg-emerald-700 text-white font-bold rounded-lg')
                            ui.label().bind_text_from(state, 'otp_timer', backward=lambda t: f'Resend in {t}s' if t > 0 else '').classes('text-xs text-gray-500')
                            ui.button('Resend OTP', on_click=lambda: handle_send_otp(state.email)).props('flat dense').classes('text-orange-600 text-xs').bind_visibility_from(state, 'otp_timer', backward=lambda t: t == 0)
                else:
                    with ui.row().classes('items-center gap-3 border-b pb-4 w-full'):
                        ui.avatar('person', color='green-800', text_color='white', size='42px')
                        with ui.column().classes('gap-0'):
                            ui.label(state.user_email).classes('font-bold text-slate-800 text-xs truncate max-w-[160px]')
                            ui.label(f'Role: {str(state.user_role).upper()}').classes('text-[10px] text-green-700 font-black uppercase')
                    
                    with ui.row().classes('items-center gap-3 w-full p-2 cursor-pointer hover:bg-green-50 rounded-xl').on('click', lambda: (setattr(state, 'current_screen', 'main_hub'), sidebar.toggle(), main_container.refresh())):
                        ui.icon('apps', size='20px').classes('text-green-800')
                        ui.label('All Dashboards').classes('text-xs font-bold text-slate-700')
                        
                    if state.user_role == 'developer':
                        with ui.row().classes('items-center gap-3 w-full p-2 cursor-pointer hover:bg-green-50 rounded-xl').on('click', lambda: (setattr(state, 'current_screen', 'manage_admins'), sidebar.toggle(), main_container.refresh())):
                            ui.icon('manage_accounts', size='20px').classes('text-green-800')
                            ui.label('Manage Admins (Dev)').classes('text-xs font-bold text-slate-700')
                            
                    ui.button('Logout App', on_click=logout).props('type=button').classes('w-full mt-4 bg-rose-600 text-white font-bold rounded-xl h-9 text-xs')
        sidebar_content()

    # --- MAIN PHONE WRAPPER FRAME ---
    with ui.column().classes('phone-wrapper'):
        
        # --- FIXED EMBEDDED GREEN TOP BAR ---
        with ui.row().classes('nav-header-bar'):
            with ui.row().classes('items-center gap-2'):
                ui.button(icon='menu', on_click=sidebar.toggle).props('flat round text-color=white dense').classes('text-white')
                ui.button(icon='refresh', on_click=lambda: main_container.refresh()).props('flat round text-color=white dense')        
                ui.label('Morya Hub Control').classes('text-white text-base font-black tracking-wide')
            
            ui.button('🏠 Home', on_click=lambda: (setattr(state, 'current_screen', 'main_hub'), main_container.refresh())) \
                .bind_visibility_from(state, 'current_screen', backward=lambda x: x == 'main_hub') \
                .classes('bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-xl shadow-none')

        # --- INTERNAL WORKSPACE MANAGER ---
        with ui.column().classes('w-full p-4 gap-4 flex-grow overflow-y-auto'):
            @ui.refreshable
            def main_container():
                if not state.is_logged_in:
                    with ui.card().classes('w-full p-6 items-center justify-center text-center bg-white border-none rounded-2xl shadow-xs mx-auto mt-10'):
                        ui.icon('lock', size='4rem').classes('text-green-700')
                        ui.label('Authentication Required').classes('text-slate-800 text-base font-bold mt-2')
                        ui.label('App open karne ke liye please left ☰ drawer se register email login verify karein.').classes('text-xs text-slate-400 mt-1 max-w-xs leading-normal')
                    return

                # 📱 SCREEN 1: MAIN ROUTER HUB VIEW
                if state.current_screen == "main_hub":
                    ui.label('My Digital Spaces').classes('w-full text-base font-black text-slate-800 mb-1 px-1')
                    
                    with ui.column().classes('w-full gap-3'):
                        with ui.card().classes('app-card w-full') \
                            .on('click', lambda: (setattr(state, 'current_screen', 'meena_tabs'), main_container.refresh())):
                            with ui.row().classes('items-center justify-between w-full no-wrap'):
                                with ui.row().classes('items-center gap-3'):
                                    ui.icon('domain', size='2.2rem').classes('text-green-700')
                                    with ui.column().classes('gap-0'):
                                        ui.label('Meena Residency').classes('text-sm font-bold text-slate-800')
                                        ui.label('Manage units & utility billing').classes('text-[10px] text-slate-400')
                                ui.icon('chevron_right', size='18px').classes('text-slate-400')

                        with ui.card().classes('app-card w-full') \
                            .on('click', lambda: (setattr(state, 'current_screen', 'education_view'), main_container.refresh())):
                            with ui.row().classes('items-center justify-between w-full no-wrap'):
                                with ui.row().classes('items-center gap-3'):
                                    ui.icon('school', size='2.2rem').classes('text-green-700')
                                    with ui.column().classes('gap-0'):
                                        ui.label('Education Portal').classes('text-sm font-bold text-slate-800')
                                        ui.label('PDF storage & exam cabinet').classes('text-[10px] text-slate-400')
                                ui.icon('chevron_right', size='18px').classes('text-slate-400')

                # 🏢 SCREEN 2: MEENA 3 OPTIONS DASHBOARD
                elif state.current_screen == "meena_tabs":
                    with ui.row().classes('w-full justify-between items-center mb-1'):
                        ui.button('⬅ Back to Hub', on_click=lambda: (setattr(state, 'current_screen', 'main_hub'), main_container.refresh())).props('flat dense').classes('text-green-800 font-bold text-xs')
                        ui.label('Meena Tabs').classes('text-[10px] font-black text-slate-400 uppercase tracking-wider')
                    
                    ui.label('Meena Options Dashboard').classes('w-full text-base font-black text-slate-800 px-1 mb-2')
                    
                    with ui.column().classes('w-full gap-3'):
                        ui.button('🏢 Rental Detail', on_click=lambda: (fetch_realtime_rooms(), setattr(state, 'current_screen', 'meena_room_select'), setattr(state, 'selected_meena_tab', 'rental_detail'), setattr(state, 'selected_room', None), setattr(state, 'room_sub_tab', None), main_container.refresh())).props('unelevated color=green-700').classes('meena-main-btn')
                        ui.button('📢 Publish Notice', on_click=lambda: (fetch_realtime_rooms(), setattr(state, 'current_screen', 'meena_room_select'), setattr(state, 'selected_meena_tab', 'publish_notice'), setattr(state, 'selected_room', None), setattr(state, 'room_sub_tab', None), main_container.refresh())).props('unelevated color=green-700').classes('meena-main-btn')
                        ui.button('📂 Other Utilities', on_click=lambda: (fetch_realtime_rooms(), setattr(state, 'current_screen', 'meena_room_select'), setattr(state, 'selected_meena_tab', 'other'), setattr(state, 'selected_room', None), setattr(state, 'room_sub_tab', None), main_container.refresh())).props('unelevated color=green-700').classes('meena-main-btn')

                # 📥 SCREEN 3: SELECT ROOM DROPBOX ONLY SCREEN
                elif state.current_screen == "meena_room_select":
                    with ui.row().classes('w-full justify-between items-center mb-2'):
                        ui.button('⬅ Back to Tabs', on_click=lambda: (setattr(state, 'current_screen', 'meena_tabs'), main_container.refresh())).props('flat dense').classes('text-green-800 font-bold text-xs')
                        ui.badge(f"{str(state.selected_meena_tab).replace('_',' ').upper()}", color='green-800').classes('text-[9px]')

                    ui.label('Select Room Number').classes('w-full text-sm font-black text-slate-800 px-1 mt-1')
                    
                    def handle_room_selection(e):
                        setattr(state, 'selected_room', e.value)
                        setattr(state, 'room_sub_tab', None)
                        setattr(state, 'member_view', 'list')
                        # 🔥 Realtime filter: Room select hote hi wahan ke active aur left heads option arrays load karega
                        fetch_room_heads_history(e.value)
                        setattr(state, 'current_screen', 'meena_original_webpage')
                        main_container.refresh()

                    def open_room(room_no):
                        setattr(state, 'selected_room', room_no)
                        setattr(state, 'room_sub_tab', None)
                        setattr(state, 'member_view', 'list')
                        fetch_room_heads_history(room_no)
                        setattr(state, 'current_screen', 'meena_original_webpage')
                        main_container.refresh()

                    def room_box(room):
                        head_name = "Vacant"
                        try:
                            renter = (
                                supabase.table('renters')
                                .select('id,head_member_id,status')
                                .eq('room_no', room)
                                .eq('status', 'ACTIVE')
                                .limit(1)
                                .execute()  )
                            if renter.data:
                                head_id = renter.data[0].get('head_member_id')
                                if head_id:
                                    head = (
                                        supabase.table('public_members')
                                        .select('name')
                                        .eq('id', head_id)
                                        .single()
                                        .execute() )
                                    if head.data:
                                        head_name = head.data.get('name', 'Vacant')
                        except:
                            pass
                        with ui.card().classes('w-full p-3 cursor-pointer bg-white border rounded-xl' ).on('click', lambda r=room: open_room(r)): 
                            with ui.row().classes( 'w-full items-center justify-between' ):
                                ui.label(f'🏠 Room {room}').classes( 'font-bold text-green-800' )
                                ui.label(head_name).classes('text-xs text-gray-600 font-medium')

                    # Ground Floor
                    with ui.card().classes('w-full p-3 bg-green-50'):
                        ui.label('Ground Floor').classes(
                            'text-[11px] text-gray-500 font-bold'
                        )

                        with ui.column().classes('w-full gap-2 mt-2'):
                            room_box('1')
                            room_box('2')
                            room_box('3')

                    # 1st Floor
                    with ui.card().classes('w-full p-3 bg-green-50 mt-2'):
                        ui.label('1st Floor').classes(
                            'text-[11px] text-gray-500 font-bold'
                        )

                        with ui.column().classes('w-full gap-2 mt-2'):
                            room_box('4')

                    # 2nd Floor
                    with ui.card().classes('w-full p-3 bg-green-50 mt-2'):
                        ui.label('2nd Floor').classes(
                            'text-[11px] text-gray-500 font-bold'
                        )

                        with ui.column().classes('w-full gap-2 mt-2'):
                            room_box('5')
                            room_box('6')

                    # 3rd Floor
                    with ui.card().classes('w-full p-3 bg-green-50 mt-2'):
                        ui.label('3rd Floor').classes(
                            'text-[11px] text-gray-500 font-bold'
                        )

                        with ui.column().classes('w-full gap-2 mt-2'):
                            room_box('7')
                        
                # 🚪 SCREEN 4: HOBAHOO MEENA ORIGINAL WEBPAGE ENGINE CODES
                elif state.current_screen == "meena_original_webpage":
                    # REALTIME DATA MAPPING INJECTOR BASED ON THE SELECTED HEAD OPTIONS
                    if state.selected_head_option and (state.renter_id != state.selected_head_option):
                        try:
                            r_lookup = supabase.table('renters').select('*').eq('id', state.selected_head_option).execute()
                            if r_lookup.data:
                                r_data = r_lookup.data[0]
                                state.renter_id = r_data['id']
                                state.room_no = r_data['room_no']
                                state.active_renter_head_id = r_data['head_member_id']
                            else:
                                state.renter_id = None
                                state.room_no = state.selected_room
                                state.active_renter_head_id = None
                        except: pass

                    # Real-time extraction of currently targeted Head name
                    family_head_name = "Family"
                    booking_date_string = "N/A"
                    renter_status_val = "ACTIVE"
                    try:
                        if state.renter_id:
                            m_lookup = supabase.table('public_members').select('name, created_at').eq('renter_id', state.renter_id).eq('relation', 'Head').execute()
                            if m_lookup.data:
                                family_head_name = m_lookup.data[0].get('name', 'Family')
                                raw_date = m_lookup.data[0].get('created_at')
                                if raw_date:
                                    booking_date_string = datetime.fromisoformat(raw_date.replace('Z', '+00:00')).strftime("%d-%b-%Y")
                            
                            status_lookup = supabase.table('renters').select('status').eq('id', state.renter_id).execute()
                            if status_lookup.data and status_lookup.data[0].get('status'):
                                renter_status_val = str(status_lookup.data[0].get('status')).upper()
                    except: pass

                    # Navigation control header logic mappings
                    with ui.row().classes('w-full justify-between items-center mb-1 no-wrap'):
                        if state.room_sub_tab is None:
                            ui.button('⬅ Change Room', on_click=lambda: (setattr(state, 'current_screen', 'meena_room_select'), setattr(state, 'selected_room', None), main_container.refresh())).props('flat dense').classes('text-green-800 font-bold text-xs')
                        else:
                            ui.button('⬅ Back', on_click=lambda: (setattr(state, 'room_sub_tab', None), main_container.refresh())).props('flat dense').classes('text-green-700 font-bold text-xs')
                        
                        # 🔥 Requirement: Room dropdown ke thik niche Select Family Head selector widget (Active upar, Left neeche)
                        def on_head_dropdown_change(e):
                            state.selected_head_option = e.value
                            state.room_sub_tab = None
                            main_container.refresh()

                        ui.select(
                            options={opt['value']: opt['label'] for opt in state.room_heads_options},
                            value=state.selected_head_option,
                            on_change=on_head_dropdown_change
                        ).props('outlined dense options-dense borderless').classes('bg-white text-xs rounded-lg max-w-[150px]')

                        # --- NEW LOGIC: ADD NEW HEAD BUTTON ---
                        # Sirf tab dikhega agar koi ACTIVE renter nahi hai
                        is_active_present = any(opt['status'] =='ACTIVE' for opt in state.room_heads_options)
                        
                        if not is_active_present:
                            def handle_new_head():
                                try:
                                    res = supabase.table("renters").insert({
                                        "room_no": state.selected_room,
                                        "status": "ACTIVE"
                                    }).execute()

                                    if not res.data:
                                        ui.notify("Renter creation failed", type="negative")
                                        return

                                    new_renter_id = res.data[0]["id"]

                                    
                                    state.room_no = state.selected_room
                                    state.active_renter_head_id = None

                                    fetch_room_heads_history(state.selected_room)

                                    state.selected_head_option = new_renter_id 
                                    state.renter_id = new_renter_id

                                    

                                    state.dynamic_family_members.clear()
                                    state.member_view = "add"

                                    main_container.refresh()

                                except Exception as e:
                                    ui.notify(f"Error: {e}", type="negative")
                            
                            ui.button('+ New Head', on_click=handle_new_head).props('flat dense').classes('text-green-700 font-bold text-xs')

                    # 🎴 CONDITION 1: AGAR KOI TAB CHOSEN NAHI HAI -> 5 TILES GRID
                    if state.room_sub_tab is None:
                        ledger_alert = False
                        try:
                            bal_rows = supabase.table('rent_ledger') \
                                .select('balance_amount') \
                                .eq('renter_id', state.renter_id) \
                                .execute()
                            overall_bal = sum(
                                float(x.get('balance_amount') or 0)
                                for x in (bal_rows.data or [])
                            )
                            state.total_overall_balance = overall_bal
                            ledger_alert = overall_bal > 500
                            
                        except:
                            pass
                        pending_payment = False

                        try:
                            pending_check = (
                                supabase.table('rent_ledger')
                                .select('id')
                                .eq('renter_id', state.renter_id)
                                .eq('deposit_status', 'Pending')
                                .limit(1)
                                .execute()
                            )
                            pending_payment = bool(pending_check.data)
                        except Exception:
                            pending_payment = False
                        ui.label(f"{family_head_name} Dashboard").classes('w-full px-1 text-base font-bold text-green-900 my-2 text-center')
                        with ui.element('div').classes('tile-grid-container my-2'):
                            with ui.element('div').classes('tile-card-btn').on('click', lambda: (setattr(state, 'room_sub_tab', 'member'), setattr(state, 'member_view', 'list'), main_container.refresh())):
                                ui.icon('person', size='2.2rem').classes('text-green-700')
                                ui.label('Member Detail').classes('font-bold text-center mt-1 text-xs text-gray-700')
                            with ui.element('div').classes('tile-card-btn').on('click', lambda: (setattr(state, 'room_sub_tab', 'electric'), setattr(state, 'billing_tab', 'current'), main_container.refresh())):
                                ui.icon('bolt', size='2.2rem').classes('text-green-700')
                                ui.label('Electric Bill').classes('font-bold text-center mt-1 text-xs text-gray-700')
                            with ui.element('div').classes('tile-card-btn').on('click', lambda: (setattr(state, 'room_sub_tab', 'gas'), setattr(state, 'billing_tab', 'current'), main_container.refresh())):
                                ui.icon('local_fire_department', size='2.2rem').classes('text-green-700')
                                ui.label('Gas Bill').classes('font-bold text-center mt-1 text-xs text-gray-700')
                            with ui.element('div').classes('tile-card-btn').on('click', lambda: (setattr(state, 'room_sub_tab', 'rent'), setattr(state, 'rent_tab', 'current'), main_container.refresh())):
                                    with ui.row().classes('items-center gap-1'):
                                        ui.icon('receipt_long', size='2.2rem').classes('text-green-700')
                                        if ledger_alert:
                                            ui.html('<div class="blink-dot"></div>')
                                    ui.label('Rent Ledger').classes('font-bold text-center mt-1 text-xs text-gray-700')
                            with ui.element('div').classes('tile-card-btn').on('click',lambda: ( setattr(state, 'room_sub_tab', 'payment'),  main_container.refresh())):
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('payments', size='2.2rem').classes('text-green-700')
                                    if pending_payment:
                                        ui.html('<span class="blink-dot-text text-red-600 font-black">P</span>')
                                ui.label('Payments').classes( 'font-bold text-center mt-1 text-xs text-gray-700')
                            with ui.element('div').classes('tile-card-btn').on('click', lambda: ( setattr(state, 'room_sub_tab', 'settings'),main_container.refresh() )):
                                ui.icon('settings', size='2.2rem').classes('text-green-700')
                                ui.label('Settings').classes( 'font-bold text-center mt-1 text-xs text-gray-700')
                    

                    # 📂 CONDITION 2: JAB KISI TILE PE CLICK HO -> DETAILS VIEW REPLACEMENT
                    else:
                        # --- 👥 TAB 1: MEMBER ENGINE LAYOUTS ---
                        if state.room_sub_tab == "member":
                            if state.member_view == "list":
                                with ui.card().classes('p-4 w-full shadow-sm bg-white border rounded-xl gap-2'):
                                    with ui.column().classes('w-full items-center mb-4 gap-2'):
                                        ui.label(f"{family_head_name} Members").classes('text-xl text-green-800 font-bold text-center w-full')
                                        with ui.row().classes('w-full justify-between items-center px-1'):
                                            ui.button('⬅ Back', on_click=lambda: (setattr(state, 'room_sub_tab', None), main_container.refresh())).props('flat dense').classes('text-green-700 font-bold text-xs')
                                            ui.button('+ Add Member', on_click=lambda: (setattr(state, 'member_view', 'add'), state.dynamic_family_members.clear(), main_container.refresh())).classes('bg-green-700 text-white font-bold text-xs')
                                    
                                    try:
                                        response = supabase.table('public_members').select('*').eq('renter_id', state.renter_id).execute() if state.renter_id else None
                                        current_members = response.data if response and response.data else []
                                        
                                        def get_sort_key(m):
                                            relation_str = str(m.get('relation', '')).strip().lower()
                                            is_head = (relation_str == 'head')
                                            try: age = int(m.get('age')) if m.get('age') is not None else 0
                                            except: age = 0
                                            priority = 1 if is_head else 2
                                            return (priority, -age)
                                            
                                        sorted_members = sorted(current_members, key=get_sort_key)
                                    except Exception as e:
                                        ui.notify(f"Database Error: {str(e)}", type='negative')
                                        sorted_members = []
                                    
                                    with ui.column().classes('w-full gap-2 mt-2'):
                                        for member in sorted_members:
                                            m_name = member.get('name', 'Unknown')
                                            m_rel = member.get('relation', 'N/A')
                                            m_id = member.get('id')
                                            m_status = member.get('status', 'Pending') 
                                            
                                            status_ball = "🟢" if m_status == "Approved" else "🔴"
                                            display_title = f"{m_name} ({m_rel}) {status_ball}"
                                            
                                            with ui.expansion(display_title, icon='person').classes('w-full border shadow-xs rounded bg-white font-bold text-base text-gray-800').props('dense header-class="text-green-800"'):
                                                with ui.grid(columns=2).classes('w-full gap-2 p-3 text-[15px] font-medium'):
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Relation:").classes('font-bold text-gray-900')
                                                        ui.label(f"{member.get('relation', 'N/A')}").classes('text-gray-600')
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Mobile No:").classes('font-bold text-gray-900')
                                                        ui.label(f"{member.get('mobile', 'N/A')}").classes('text-gray-600')
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Age:").classes('font-bold text-gray-900')
                                                        ui.label(f"{member.get('age', 'N/A')}").classes('text-gray-600')
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Gender:").classes('font-bold text-gray-900')
                                                        ui.label(f"{member.get('gender', 'N/A')}").classes('text-gray-600')
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Religion:").classes('font-bold text-gray-900')
                                                        ui.label(f"{member.get('religion', 'N/A')}").classes('text-gray-600')
                                                    with ui.row().classes('gap-1'):
                                                        ui.label("Aadhaar No:").classes('font-bold text-gray-900')
                                                        ui.label("[Aadhaar Redacted]").classes('text-gray-600')
                                                    if member.get('whatsapp'):
                                                        with ui.row().classes('gap-1'):
                                                            ui.label("WhatsApp:").classes('font-bold text-gray-900')
                                                            ui.label(f"{member.get('whatsapp')}").classes('text-gray-600')
                                                    if member.get('occupation'):
                                                        with ui.row().classes('gap-1'):
                                                            ui.label("Occupation:").classes('font-bold text-gray-900')
                                                            ui.label(f"{member.get('occupation')}").classes('text-gray-600')
                                                    
                                                with ui.column().classes('w-full p-3 bg-gray-50 border-t text-[14px] font-normal gap-1'):
                                                    ui.label('Address Details:').classes('font-bold text-gray-900 text-sm border-b pb-1 mb-1')
                                                    
                                                    raw_address = member.get('address', 'Meena Residency')
                                                    if raw_address == "Same as Head":
                                                        with ui.row().classes('items-center no-wrap gap-1'):
                                                            ui.label("Current Address:").classes('font-bold text-gray-900')
                                                            ui.label("Same as Family Head Address").classes('text-emerald-700 font-medium')
                                                    elif "Panchayat:" in raw_address or "Dist:" in raw_address:
                                                        addr_dict = {}
                                                        parts = raw_address.split(',')
                                                        if parts and ":" not in parts[0]:
                                                            addr_dict['Vill/Flat No'] = parts[0].strip()
                                                        for part in parts:
                                                            if ":" in part:
                                                                k, v = part.split(':', 1)
                                                                addr_dict[k.strip()] = v.strip()
                                                        
                                                        labels_to_show = [
                                                            ('Vill/Flat No', 'Village / Flat No'),
                                                            ('Panchayat', 'Panchayat'),
                                                            ('Block', 'Block'),
                                                            ('PS', 'Police Station (PS)'),
                                                            ('PO', 'Post Office (PO)'),
                                                            ('Dist', 'District'),
                                                            ('State', 'State'),
                                                            ('Pin', 'Pincode')
                                                        ]
                                                        for key_lbl, display_lbl in labels_to_show:
                                                            val = addr_dict.get(key_lbl, addr_dict.get(display_lbl, ''))
                                                            if val:
                                                                with ui.row().classes('items-center no-wrap gap-1'):
                                                                    ui.label(f"{display_lbl}:").classes('font-bold text-gray-900')
                                                                    ui.label(val).classes('text-emerald-700 font-medium')
                                                    else:
                                                        with ui.row().classes('items-center no-wrap gap-1'):
                                                            ui.label("Current Address:").classes('font-bold text-gray-900')
                                                            ui.label(raw_address).classes('text-emerald-700 font-medium')

                                                # --- ACTIONS CONTROL PANEL ---
                                                ui.separator().classes('my-1')
                                                with ui.column().classes('w-full p-3 bg-slate-50 border-t gap-2'):
                                                    ui.label('Actions Control Panel').classes('text-xs font-bold text-green-900 uppercase tracking-wider')
                                                    
                                                    with ui.row().classes('w-full items-center justify-between flex-wrap gap-2'):
                                                        def handle_status_toggle(e, member_uuid=m_id):
                                                            new_status = "Approved" if e.value else "Pending"
                                                            try:
                                                                supabase.table('public_members').update({"status": new_status}).eq('id', member_uuid).execute()
                                                                ui.notify(f"Status updated to {new_status}!", type='positive')
                                                                main_container.refresh()
                                                            except Exception as err:
                                                                ui.notify(f"Toggle failed: {err}", type='negative')

                                                        is_approved = (m_status == "Approved")
                                                        ui.switch('Approved Status', value=is_approved, on_change=lambda e, uuid=m_id: handle_status_toggle(e, uuid)).props('dense color=green').classes('text-xs font-bold text-slate-700')
                                                        
                                                        with ui.row().classes('gap-2'):
                                                            def trigger_modify(m_data=member):
                                                                raw_addr = m_data.get('address', '')
                                                                v_val, pan_val, blk_val, ps_val, po_val, dt_val, st_val, pin_val = "", "", "", "", "", "", "", ""
                                                                
                                                                if "Panchayat:" in raw_addr or "Dist:" in raw_addr:
                                                                    parts = raw_addr.split(',')
                                                                    if parts and ":" not in parts[0]:
                                                                        v_val = parts[0].strip()
                                                                    for part in parts:
                                                                        if ":" in part:
                                                                            k, v = part.split(':', 1)
                                                                            k = k.strip()
                                                                            v = v.strip()
                                                                            if k in ['Vill/Flat No', 'Village / Flat No']: v_val = v
                                                                            elif k == 'Panchayat': pan_val = v
                                                                            elif k == 'Block': blk_val = v
                                                                            elif k == 'PS': ps_val = v
                                                                            elif k == 'PO': po_val = v
                                                                            elif k == 'Dist': dt_val = v
                                                                            elif k == 'State': st_val = v
                                                                            elif k == 'Pin': pin_val = v
                                                                else:
                                                                    v_val = raw_addr

                                                                state.dynamic_family_members = [{
                                                                    'edit_id': m_data.get('id'),
                                                                    'name_v': m_data.get('name', ''),
                                                                    'rel_v': m_data.get('relation', 'Wife'),
                                                                    'gen_v': m_data.get('gender', 'Male'),
                                                                    'age_v': str(m_data.get('age', '')),
                                                                    'mob_v': m_data.get('mobile', ''),
                                                                    'adh_v': m_data.get('aadhaar', ''),
                                                                    'relig_v': m_data.get('religion', ''),
                                                                    'v_v': v_val, 'panch_v': pan_val, 'block_v': blk_val,
                                                                    'ps_v': ps_val, 'po_v': po_val, 'dt_v': dt_val,
                                                                    'st_v': st_val, 'pin_v': pin_val,
                                                                    'show_addr': m_data.get('relation') in ['Staff', 'Others', 'Head']
                                                                }]
                                                                setattr(state, 'member_view', 'add')
                                                                main_container.refresh()

                                                            ui.button('Modify', on_click=lambda m=member: trigger_modify(m)).props('dense unelevated color=blue-600 icon=edit').classes('text-xs font-bold rounded-lg px-3')
                                                            
                                                            def trigger_delete(member_uuid=m_id, name=m_name, relation=m_rel):
                                                                if str(relation).strip().lower() == 'head' and state.user_role != 'developer':
                                                                    ui.notify('Access Denied: Only Developer can delete the Family Head!', type='negative')
                                                                    return

                                                                with ui.dialog() as dialog, ui.card().classes('p-4 items-center gap-3'):
                                                                    ui.label(f"⚠️ Confirm Delete?").classes('font-black text-red-600 text-lg')
                                                                    ui.label(f"Kya aap sach me {name} ka record permanent delete karna chahte hain?").classes('text-xs text-center text-slate-500')
                                                                    with ui.row().classes('gap-2 mt-2 w-full justify-center'):
                                                                        def conf_del():
                                                                            try:
                                                                                supabase.table('public_members').delete().eq('id', member_uuid).execute()
                                                                                ui.notify('Member Record Deleted Successfully!', type='positive')
                                                                                dialog.close()
                                                                                main_container.refresh()
                                                                            except Exception as err:
                                                                                ui.notify(f"Delete Error: {err}", type='negative')
                                                                        ui.button('YES, DELETE', on_click=conf_del).props('unelevated color=red-600').classes('text-xs font-bold')
                                                                        ui.button('CANCEL', on_click=dialog.close).props('flat color=gray').classes('text-xs font-bold')
                                                                dialog.open()

                                                            ui.button('Delete', on_click=lambda uuid=m_id: trigger_delete(uuid)).props('dense unelevated color=red-600 icon=delete').classes('text-xs font-bold rounded-lg px-3')
                            
                            elif state.member_view == "add":
                                with ui.column().classes('w-full max-w-2xl mx-auto mt-1 gap-4'):
                                    with ui.card().classes('p-4 w-full shadow-md border-t-4 border-blue-600 bg-white'):
                                        is_editing = 'edit_id' in state.dynamic_family_members[0] if state.dynamic_family_members else False
                                        title_text = 'Modify Member Record' if is_editing else ('Create Head Of Family' if not state.active_renter_head_id else 'Add Family Members')
                                        ui.label(title_text).classes('text-lg font-bold text-slate-800 mb-2')
                                        
                                        @ui.refreshable
                                        def sub_members_ui():
                                            if not state.dynamic_family_members:
                                                if not state.active_renter_head_id:
                                                    state.dynamic_family_members.append({
                                                        'name_v': '', 'rel_v': 'Head', 'gen_v': 'Male', 'age_v': '', 'mob_v': '', 'adh_v': '',
                                                        'show_so': False, 'show_staff_so': False, 'show_addr': True,
                                                        'v_v': '', 'panch_v': '', 'block_v': '', 'ps_v': '', 'po_v': '', 'dt_v': '', 'st_v': '', 'pin_v': ''
                                                    })
                                                else:
                                                    state.dynamic_family_members.append({
                                                        'name_v': '', 'rel_v': 'Wife', 'gen_v': 'Female', 'age_v': '', 'mob_v': '', 'adh_v': '',
                                                        'show_so': False, 'show_staff_so': False, 'show_addr': False,
                                                        'v_v': '', 'panch_v': '', 'block_v': '', 'ps_v': '', 'po_v': '', 'dt_v': '', 'st_v': '', 'pin_v': ''
                                                    })

                                            for idx, m_state in enumerate(state.dynamic_family_members):
                                                with ui.row().classes('w-full items-center justify-between my-2 bg-blue-50 p-1 rounded border-l-4 border-blue-500'):
                                                    ui.label(f"Family Member Fields").classes('text-xs font-bold text-blue-800')
                                                    if len(state.dynamic_family_members) > 1 and not is_editing:
                                                        ui.button('X', on_click=lambda i=idx: (state.dynamic_family_members.pop(i), sub_members_ui.refresh())).classes('bg-red-600 text-white font-bold text-[10px] px-2 py-0.5 rounded shadow-sm')
                                                
                                                with ui.card().classes('w-full p-3 bg-gray-50 border border-gray-200 rounded-lg shadow-inner mb-2'):
                                                    def on_sub_rel_change(e, s=m_state):
                                                        s['rel_v'] = e.value
                                                        s['show_so'] = e.value == 'Husband'
                                                        s['show_staff_so'] = e.value in ['Staff', 'Others']
                                                        s['show_addr'] = e.value in ['Staff', 'Others', 'Head']
                                                        sub_members_ui.refresh()

                                                    with ui.grid(columns=2).classes('w-full gap-2'):
                                                        ui.input('Member Name').props('outlined dense').bind_value(m_state, 'name_v')
                                                        ui.select(['Head','Wife','Husband','Son','Daughter','Grandfather','Grandmother','Grandson','Granddaughter','Staff','Others'], label='Relation', value=m_state['rel_v'], on_change=lambda e, s=m_state: on_sub_rel_change(e, s)).props('outlined dense')
                                                    
                                                    with ui.grid(columns=2).classes('w-full gap-2 mt-2'):
                                                        ui.select(['Female', 'Male', 'Other'], label='Gender', value=m_state['gen_v']).props('outlined dense').on('value_change', lambda e, s=m_state: s.update({'gen_v': e.value}))
                                                        ui.input('Age').props('outlined dense type="number"').bind_value(m_state, 'age_v')
                                                        ui.input('Mobile').props('outlined dense mask="##########"').bind_value(m_state, 'mob_v')
                                                        ui.input('Aadhaar').props('outlined dense mask="####-####-####"').bind_value(m_state, 'adh_v')
                                                    
                                                    if m_state.get('show_addr') or m_state.get('rel_v') == 'Head':
                                                        with ui.column().classes('w-full mt-2 p-2 bg-white rounded border border-emerald-100'):
                                                            ui.input('Religion').props('outlined dense placeholder="e.g., Hindu"').classes('w-full mb-2').bind_value(m_state, 'relig_v')
                                                            ui.label('Address Details').classes('text-[10px] font-bold text-emerald-600')
                                                            with ui.grid(columns=2).classes('w-full gap-2'):
                                                                ui.input('Village / Flat No').props('outlined dense').bind_value(m_state, 'v_v')
                                                                ui.input('Panchayat').props('outlined dense').bind_value(m_state, 'panch_v')
                                                                ui.input('Block').props('outlined dense').bind_value(m_state, 'block_v')
                                                                ui.input('Police Station (PS)').props('outlined dense').bind_value(m_state, 'ps_v')
                                                                ui.input('Post Office (PO)').props('outlined dense').bind_value(m_state, 'po_v')
                                                                ui.input('District').props('outlined dense').bind_value(m_state, 'dt_v')
                                                                ui.input('State').props('outlined dense').bind_value(m_state, 'st_v')
                                                                ui.input('Pincode').props('outlined dense').bind_value(m_state, 'pin_v')
                                        
                                        sub_members_ui()

                                        if not is_editing:
                                            def add_fam():
                                                if len(state.dynamic_family_members) < 5:
                                                    state.dynamic_family_members.append({
                                                        'name_v': '', 'rel_v': 'Wife', 'gen_v': 'Female', 'age_v': '', 'mob_v': '', 'adh_v': '', 'show_so': False, 'show_staff_so': False, 'show_addr': False,
                                                        'v_v': '', 'panch_v': '', 'block_v': '', 'ps_v': '', 'po_v': '', 'dt_v': '', 'st_v': '', 'pin_v': ''
                                                    })
                                                    sub_members_ui.refresh()
                                            ui.button('Add more Member', on_click=add_fam).classes('bg-blue-600 text-white font-bold text-xs rounded h-8 mx-auto block my-3')

                                        def save_all():
                                            if not state.dynamic_family_members: return
                                            has_valid_member = any(str(m.get('name_v', '')).strip() != '' for m in state.dynamic_family_members)
                                            if not has_valid_member:
                                                ui.notify('Member Name is required!', type='warning')
                                                return
                                            try:
                                                for m in state.dynamic_family_members:
                                                    member_name = str(m.get('name_v', '')).strip()
                                                    if not member_name: continue
                                                    r_val = m.get('rel_v', 'Wife')
                                                    
                                                    if r_val in ['Staff', 'Others', 'Head']:
                                                        sub_addr = f"{m.get('v_v','')}, Panchayat: {m.get('panch_v','')}, Block: {m.get('block_v','')}, PO: {m.get('po_v','')}, PS: {m.get('ps_v','')}, Dist: {m.get('dt_v','')}, State: {m.get('st_v','')}, Pin: {m.get('pin_v','')}"
                                                        sub_addr = sub_addr.strip().strip(',')
                                                    else:
                                                        sub_addr = "Same as Head"
                                                    
                                                    # 🔥 FIXED CONSTRAINT ENFORCER FOR NEW FAMILY HEAD
                                                    # Agar Relation 'Head' hai, toh explicit self-referencing loop se bachne ke liye None (NULL) bhejenge.
                                                    head_id_value = None if r_val == 'Head' else (state.active_renter_head_id if state.active_renter_head_id else None)

                                                    row_data = {
                                                        "name": member_name, "relation": r_val, "father_husband_name": None,
                                                        "age": int(m['age_v']) if m.get('age_v') and str(m['age_v']).isdigit() else None,
                                                        "gender": m.get('gen_v', 'Female'), "mobile": m.get('mob_v') if m.get('mob_v') else None, 
                                                        "whatsapp": None, "aadhaar": m.get('adh_v') if m.get('adh_v') else None,
                                                        "religion": str(m.get('relig_v', '')).strip() or 'N/A', "occupation": None, "address": sub_addr,
                                                        "head_id": head_id_value, "renter_id": state.renter_id
                                                    }
                                                    
                                                    if 'edit_id' in m: 
                                                        supabase.table('public_members').update(row_data).eq('id', m['edit_id']).execute()
                                                        send_push( state.renter_id, "New Member Added",f"Room {state.selected_room} New member added")
                                                        if r_val == 'Head':
                                                            supabase.table('renters').update({'head_member_id': m['edit_id']}).eq('id', state.renter_id).execute()
                                                            state.active_renter_head_id = m['edit_id']
                                                    else: 
                                                        row_data["status"] = "Pending" 
                                                        insert_response = supabase.table('public_members').insert([row_data]).execute()
                                                        if r_val == 'Head' or not state.active_renter_head_id:
                                                            head_uuid = insert_response.data[0]['id']
                                                            supabase.table('renters').update({'head_member_id': head_uuid}).eq('id', state.renter_id).execute()
                                                            state.active_renter_head_id = head_uuid
                                                
                                                ui.notify('Record Processed successfully!', type='positive')
                                                setattr(state, 'member_view', 'list')
                                                main_container.refresh()
                                            except Exception as ex:
                                                ui.notify(f"Database Error: {str(ex)}", type='negative')

                                        with ui.row().classes('w-full mt-2 gap-2 mb-6'):
                                            ui.button('SAVE RECORD', on_click=save_all).classes('bg-green-700 text-white flex-grow font-bold text-xs h-9')
                                            ui.button('CANCEL', on_click=lambda: (setattr(state, 'member_view', 'list'), main_container.refresh())).classes('bg-gray-400 text-white text-xs h-9')
                        # --- 💵 DETAIL VIEW: RENT LEDGER SHEETS ---
                        elif state.room_sub_tab == "rent":
                            
                            state.bill_type = "Rent"
                            with ui.card().classes('p-4 w-full max-w-4xl shadow-md mx-auto mt-2 bg-white'):
                                ui.label('Rent Ledger').classes('text-xl text-green-800 font-bold mb-4 text-center w-full')
                                
                                # 1. Tab Navigation (Electric/Gas jaisa)
                                # Rent Ledger UI me tabs update karein
                                with ui.row().classes('w-full p-1 bg-gray-100 rounded-lg shadow-inner mb-4 border'):
                                    ui.button('📅 CURRENT', on_click=lambda: (setattr(state, 'rent_tab', 'current'), main_container.refresh())).classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.rent_tab != 'current' else 'unelevated color="green-700" text-color=white')
                                    ui.button('📜 HISTORY', on_click=lambda: (setattr(state, 'rent_tab', 'history'), main_container.refresh())).classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.rent_tab != 'history' else 'unelevated color="green-700" text-color=white')
                                    with ui.row().classes('items-center gap-1 flex-1'):
                                      ui.button('📊 LEDGER', on_click=lambda: (setattr(state, 'rent_tab', 'ledger'), main_container.refresh())).classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.rent_tab != 'ledger' else 'unelevated color="green-700" text-color=white')
                                      if getattr(state, 'total_overall_balance', 0) > 500:
                                                ui.html('<div class="blink-dot"></div>')
                                                   
                                    
                                if state.rent_tab == "current":
                                    # 1. Data Fetching
                                    rent_row = None
                                    electric_auto, gas_auto = 0, 0
                                    try:
                                        # Rent Ledger check
                                        resp = supabase.table('rent_ledger').select('*').eq('renter_id', state.renter_id) \
                                            .eq('bill_month', state.selected_month).eq('bill_year', datetime.now().year).maybe_single().execute()
                                        if resp and hasattr(resp, 'data'):
                                              rent_row = resp.data
                                        
                                        # Utility Bill auto-fetch: Renter, Month, Year match karke total_amount uthao
                                        bill_resp = supabase.table('utility_billing_ledger') \
                                            .select('bill_type, total_amount') \
                                            .eq('renter_id', state.renter_id) \
                                            .eq('bill_month', state.selected_month) \
                                            .eq('bill_year', datetime.now().year).execute()
                                        if bill_resp and hasattr(bill_resp, 'data') and bill_resp.data:
                                            electric_auto = sum([float(b.get('total_amount', 0)) for b in bill_resp.data if b.get('bill_type') == 'Electric'])
                                            gas_auto = sum([float(b.get('total_amount', 0)) for b in bill_resp.data if b.get('bill_type') == 'Gas'])
                                            
                                    except Exception as e:
                                        print(f"DEBUG: Fetch Error: {e}")

                                    # 2. UI Layout
                                    with ui.card().classes('p-4 w-full max-w-4xl shadow-md mx-auto mt-2 bg-white'):
                                        ui.label(f'Rent Ledger: {state.selected_month} {datetime.now().year}').classes('text-xl text-green-800 font-bold mb-4 text-center w-full')
                                        edit_mode = getattr(state, 'edit_mode', False)

                                        if rent_row and not edit_mode:
                                            # SUMMARY VIEW
                                            with ui.card().classes('w-full p-4 border-2 border-green-100 rounded-xl bg-green-50'):
                                                ui.label(f"Flat Rent: ₹{rent_row.get('flat_bill', 0)}").classes('font-bold')
                                                ui.label(f"Electric: ₹{rent_row.get('electric_bill', 0)}").classes('font-bold')
                                                ui.label(f"Gas: ₹{rent_row.get('gas_bill', 0)}").classes('font-bold')
                                                ui.label(f"Extra: ₹{rent_row.get('other_charge', 0)}").classes('font-bold')
                                                ui.separator().classes('my-2')
                                                ui.label(f"TOTAL Dues: ₹{rent_row.get('total_charge', 0)}").classes('text-lg font-black text-green-900')
                                            
                                            with ui.row().classes('w-full mt-4 gap-2'):
                                                ui.button('✏️ EDIT', on_click=lambda: (setattr(state, 'edit_mode', True), main_container.refresh())).classes('flex-1 bg-orange-500')
                                                ui.button( ' Share💬',  on_click=lambda: share_current_rent_whatsapp(rent_row,state.renter_id)).props('flat color=green icon=fab fa-whatsapp')    
                                        else:

                                                # Inputs: Auto-fetch values bind ki gayi hain
                                                base_rent = ui.input('Flat Base Rent', value=rent_row.get('flat_bill', '') if rent_row else '').props('outlined dense type="number"')
                                                elec_val = rent_row.get('electric_bill', electric_auto) if rent_row else electric_auto
                                                elec_input = ui.input('Electric Bill', value=elec_val).props('outlined dense type="number"')
                                                
                                                gas_val = rent_row.get('gas_bill', gas_auto) if rent_row else gas_auto
                                                gas_input = ui.input('Gas Bill', value=gas_val).props('outlined dense type="number"')
                                            
                                                extra_input = ui.input('Other Charges', value=rent_row.get('other_charge', '0') if rent_row else '0').props('outlined dense type="number"')
                                                
                                                # Live Calculation
                                                total_label = ui.label().classes('text-lg font-black text-green-900 mt-2')
                                                def update_calc(*args):
                                                    total = float(base_rent.value or 0) + float(elec_input.value or 0) + float(gas_input.value or 0) + float(extra_input.value or 0)
                                                    total_label.set_text(f"Total Due: ₹{total}")
                                                for i in [base_rent, elec_input, gas_input, extra_input]:
                                                    i.on('change', update_calc)
                                                update_calc()

                                                def save_rent():
                                                    payload = {
                                                        "renter_id": state.renter_id,
                                                        "room_no": state.selected_room,
                                                        "bill_month": state.selected_month,
                                                        "bill_year": datetime.now().year,
                                                        "flat_bill": float(base_rent.value or 0),
                                                        "electric_bill": float(elec_input.value or 0),
                                                        "gas_bill": float(gas_input.value or 0),
                                                        "other_charge": float(extra_input.value or 0),
                                                    }
                                                    try:
                                                        if rent_row:
                                                            supabase.table('rent_ledger').update(payload).eq('id', rent_row['id']).execute()
                                                        else:
                                                            supabase.table('rent_ledger').insert(payload).execute()
                                                            send_push( state.renter_id,  "Payment Pending",  f"Room {state.selected_room} payment request pending")
                                                        setattr(state, 'edit_mode', False)
                                                        ui.notify("Rent Ledger Saved!", type="positive")
                                                        main_container.refresh()
                                                    except Exception as e:
                                                        ui.notify(f"Save Error: {e}", type="negative")

                                                with ui.row().classes('w-full mt-4 gap-2'):
                                                    ui.button('SAVE', on_click=save_rent).classes('flex-1 bg-green-700 text-white')
                                                    if rent_row:
                                                        ui.button('BACK', on_click=lambda: (setattr(state, 'edit_mode', False), main_container.refresh())).classes('flex-1 bg-gray-400 text-white')    
                                elif state.rent_tab == "history":
                                    # 1. Database se unique Month-Year options fetch karo
                                    options = []
                                    try:
                                        res = supabase.table('rent_ledger') \
                                            .select('bill_month, bill_year') \
                                            .eq('renter_id', state.renter_id) \
                                            .execute()
                                        
                                        if res.data:
                                            # Unique Month-Year list generate karo
                                            raw_list = [f"{r['bill_month']} {r['bill_year']}" for r in res.data]
                                            options = sorted(list(set(raw_list)), reverse=True)
                                    except: pass

                                    # 2. Dropdown UI
                                    current_options = options if options else ["N/A"]
                                    if state.history_month not in current_options:
                                        state.history_month = current_options[0]
                                    
                                    ui.select(
                                        options=current_options, 
                                        value=state.history_month, 
                                        label="Select Month/Year", 
                                        on_change=lambda e: (setattr(state, 'history_month', e.value), main_container.refresh())
                                    ).props('outlined dense').classes('w-full mb-4')

                                    # 3. Data Fetching Logic (Selected Month se match karke)
                                    hist_data = None
                                    if current_options != ["N/A"]:
                                        try:
                                            parts = state.history_month.split()
                                            q_month, q_year = parts[0], int(parts[1])
                                            resp = supabase.table('rent_ledger') \
                                                .select('*') \
                                                .eq('renter_id', state.renter_id) \
                                                .eq('bill_month', q_month) \
                                                .eq('bill_year', q_year).single().execute()
                                            hist_data = resp.data
                                        except: pass

                                    # 4. Display UI
                                    if hist_data:
                                        with ui.card().classes('w-full p-4 bg-white border rounded-lg shadow-sm'):
                                            ui.label(f"{state.history_month} Rent detail").classes('text-green-800 font-bold mb-2 underline')
                                            with ui.column().classes('gap-1'):
                                                ui.label(f"Flat  Rent: ₹ {hist_data.get('flat_bill', 0)}")
                                                ui.label(f"Electric Bill: ₹ {hist_data.get('electric_bill', 0)}")
                                                ui.label(f"Gas Bill: ₹ {hist_data.get('gas_bill', 0)}")
                                                ui.label(f"Extra Charges: ₹ {hist_data.get('other_charge', 0)}")
                                                ui.separator().classes('my-2')
                                                ui.label(f"TOTAL Dues: ₹ {hist_data.get('total_charge', 0)}").classes('text-lg font-black text-green-800')
                                    else:
                                        ui.label("Is mahine ka koi record nahi mila.").classes('text-center text-gray-500 mt-10')    
                        
                                elif state.rent_tab == "ledger":
                                        ui.label("Balance Sheet").classes('text-green-800 font-bold mb-2 text-center w-full')
                                                
                                        
                                        rows_data = []
                                        try:
                                            resp = supabase.table('rent_ledger') \
                                                .select('*') \
                                                .eq('renter_id', state.renter_id) \
                                                .order('bill_year', desc=True) \
                                                .order('bill_month', desc=True) \
                                                .execute()
                                            rows_data = resp.data if resp.data else []
                                        except Exception as e:
                                            ui.notify(f"Error fetching ledger: {e}", type='negative')

                                        total_overall_balance = 0
                                    
                                        if rows_data:
                                            table_rows = []                                   
                                            for r in rows_data:
                                                total = float(r.get('total_charge') or 0)
                                                bal = float(r.get('balance_amount') or 0)
                                                
                                                # Due Date (created_at)
                                                raw_created = r.get('created_at', '')
                                                created_dt = "N/A"
                                                if raw_created:
                                                    try: created_dt = datetime.fromisoformat(raw_created.replace('Z', '+00:00')).strftime('%d-%b')
                                                    except: pass
                                                # Paid Amount aur Deposit Date
                                                deposit_status = str(r.get('deposit_status') or '').lower()
                                                if deposit_status == 'approved':
                                                    paid_amt = float(r.get('deposite') or 0)
                                                    dep_date_raw = r.get('deposit_date')
                                                    dep_date_fmt = "N/A"
                                                    if dep_date_raw:
                                                        try:
                                                            dep_date_fmt = datetime.strptime(
                                                                dep_date_raw,
                                                                '%Y-%m-%d'
                                                            ).strftime('%d-%b')
                                                        except:
                                                            dep_date_fmt = dep_date_raw
                                                else:
                                                    paid_amt = "N/A"
                                                    dep_date_fmt = "N/A"           
                                                total_overall_balance += bal
                                                state.total_overall_balance = total_overall_balance
                                                table_rows.append({
                                                    'month': f"{r.get('bill_month')} {r.get('bill_year')}",
                                                    'due_col': {'amount': total, 'date': created_dt},
                                                    'paid_col': {'amount': paid_amt, 'date': dep_date_fmt},
                                                    'bal': bal
                                                })

                                            columns = [
                                                {'name': 'month', 'label': 'Month', 'field': 'month', 'align': 'left'},
                                                {'name': 'due_col', 'label': 'Dues ', 'field': 'due_col', 'align': 'right'},
                                                {'name': 'paid_col', 'label': 'Deposite ', 'field': 'paid_col', 'align': 'right'},
                                                {'name': 'bal', 'label': 'Bal', 'field': 'bal', 'align': 'right'},
                                            ]

                                            table = ui.table(columns=columns, rows=table_rows, row_key='month').classes('w-full')
                                            
                                            # Slot for Due (Created Date)
                                            table.add_slot('body-cell-due_col', '''
                                                <q-td :props="props"><div class="column items-end">
                                                    <span class="font-bold">{{ props.row.due_col.amount }}</span>
                                                    <span class="text-[10px] text-gray-500">{{ props.row.due_col.date }}</span>
                                                </div></q-td>
                                            ''')
                                            
                                            # Slot for Paid (Deposit Date)
                                            table.add_slot('body-cell-paid_col', '''
                                                <q-td :props="props"><div class="column items-end">
                                                    <span class="font-bold text-emerald-600">{{ props.row.paid_col.amount }}</span>
                                                    <span class="text-[10px] text-gray-500">{{ props.row.paid_col.date }}</span>
                                                </div></q-td>
                                            ''')
                                            with ui.card().classes( 'w-full bg-green-50 p-3 mt-3 border-2 border-green-200'):
                                                with ui.row().classes( 'w-full items-center justify-between'):
                                                    ui.label(f"Overall Balance: ₹{total_overall_balance}"  ).classes(    'text-lg font-black text-green-900')
                                                    ui.button( 'Share 💬', on_click=lambda: share_ledger_whatsapp(  rows_data,  total_overall_balance, state.renter_id )).props('flat color=green').classes('text-green-600')

                                        else:
                                            ui.label("Koi record nahi mila.").classes('text-gray-400 text-center w-full mt-5')
                                    
                        elif state.room_sub_tab == "payment":
                                        def open_add_payment_dialog():
                                            ledger_rows = supabase.table('rent_ledger') \
                                                .select('id,bill_month,bill_year') \
                                                .eq('renter_id', state.renter_id) \
                                                .execute()
                                            options = {
                                                str(r['id']):
                                                f"{r['bill_month']} {r['bill_year']}"
                                                for r in (ledger_rows.data or [])
                                            }
                                            with ui.dialog() as dialog, ui.card().classes('w-80 p-4'):
                                                ui.label('Add Payment').classes(
                                                    'text-lg font-bold text-green-800'
                                                )

                                                month_select = ui.select(
                                                    options=options,
                                                    label='Bill Month'
                                                ).props('outlined dense')

                                                amount_input = ui.input(
                                                    'Amount'
                                                ).props('outlined dense type=number')

                                                def save_payment():
                                                    if not month_select.value:
                                                        ui.notify(
                                                            'Select Month',
                                                            type='warning'
                                                        )
                                                        return
                                                    supabase.table('rent_ledger').update({
                                                        'deposite': float(amount_input.value or 0),
                                                        'deposit_status': 'Approved',
                                                        'deposit_date': datetime.now().date().isoformat(),
                                                        'approved_date': datetime.now().date().isoformat()
                                                    }).eq(
                                                        'id',
                                                        int(month_select.value)
                                                    ).execute()
                                                    dialog.close()
                                                    ui.notify(
                                                        'Payment Saved',
                                                        type='positive'
                                                    )
                                                    main_container.refresh()
                                                with ui.row().classes(
                                                    'w-full justify-end gap-2'
                                                ):
                                                    ui.button(
                                                        'Cancel',
                                                        on_click=dialog.close
                                                    )
                                                    ui.button(
                                                        'Save ',
                                                        on_click=save_payment
                                                    ).classes(
                                                        'bg-green-600 text-white'
                                                    )
                                            dialog.open()
                                        with ui.row().classes('w-full justify-between items-center mt-2 mb-2'):
                                            ui.label("Payment Approvals").classes(
                                                'text-green-800 font-bold'
                                            )

                                            ui.button(
                                                '+ Add Pay',
                                                on_click=open_add_payment_dialog
                                            ).classes(
                                                'bg-green-600 text-white font-bold text-xs h-8'
                                            )

                                        
                                        # Data Fetching
                                        payment_data = []
                                        try:
                                            resp = supabase.table('rent_ledger') \
                                                .select('*') \
                                                .eq('renter_id', state.renter_id) \
                                                .order('bill_year', desc=True) \
                                                .order('bill_month', desc=True) \
                                                .execute()
                                            payment_data = resp.data if resp.data else []
                                            payment_data.sort(  key=lambda x: ( 0 if str(x.get('deposit_status', '')).lower() == 'pending' else 1, -(x.get('bill_year') or 0)))
                                        except Exception as e:
                                            ui.notify(f"Error: {e}", type='negative')

                                        if not payment_data:
                                            ui.label("Koi payment record nahi mila.").classes('text-gray-400 text-center w-full mt-5')
                                        else:
                                            for p in payment_data:
                                                # Data Extraction
                                                amt = p.get('deposite', 0)
                                                d_date = p.get('deposit_date') if p.get('deposit_date') else "N/A"
                                                status = p.get('deposit_status') if p.get('deposit_status') else "Pending"
                                                
                                                # Expansion Box
                                                status = str(p.get('deposit_status') or 'Pending')
                                                ball = "🟢" if status.lower() == "approved" else "🔴"
                                                title = (f"{p.get('bill_month')} {p.get('bill_year')} "
                                                        f"- {status} {ball}")
                                                with ui.expansion( title, icon='payments').classes('w-full border rounded-lg bg-white my-1'):
                                                    with ui.column().classes('w-full p-3 gap-2'):
                                                        # Details Row
                                                        with ui.row().classes('w-full  items-center gap-2'):
                                                            ui.label("Amount:").classes('font-bold text-gray-700  min-w-[60px]')
                                                            amount_input = ui.input(
                                                                value=str(p.get('deposite') or 0)
                                                            ).props('dense outlined type=number').classes('w-28')
                                                        with ui.row().classes('w-full items-center gap-2'):
                                                            ui.label("Date:").classes('font-bold text-gray-700 min-w-[45px]')
                                                            ui.label(f"{d_date}").classes('text-gray-900')
                                                        with ui.row().classes('w-full justify-between'):
                                                            ui.label("Status:").classes('font-bold text-gray-700')
                                                            ui.label(f"{status}").classes('font-bold text-blue-600')
                                                        approved_date = p.get('approved_date')
                                                        if status.lower() == 'approved':
                                                            with ui.row().classes('w-full items-center gap-2'):
                                                                ui.label("Approved:").classes(
                                                                    'font-bold text-green-700 min-w-[75px]'
                                                                )
                                                                ui.label(
                                                                    approved_date if approved_date else "N/A"
                                                                ).classes('text-green-700')


                                                        # Action Buttons
                                                        with ui.row().classes('w-full justify-center gap-2 mt-3'):
                                                            def update_payment_status(row_id, new_status, amount_val):
                                                                try:
                                                                    payload = {
                                                                        'deposite': float(amount_val or 0),
                                                                        'deposit_status': new_status
                                                                    }
                                                                    if new_status.lower() == 'approved':
                                                                        payload['approved_date'] = datetime.now().date().isoformat()
                                                                    supabase.table('rent_ledger').update(payload)\
                                                                        .eq('id', row_id).execute()
                                                                    ui.notify(
                                                                        f"Status Updated to {new_status}",
                                                                        type='positive'
                                                                    )
                                                                    main_container.refresh()
                                                                except Exception as e:
                                                                    ui.notify(f"Error: {e}", type='negative')
                                                            
                                                            ui.button('Approve', on_click=lambda  id=p['id'], inp=amount_input: update_payment_status(    id,  'Approved', inp.value)
                                                                ).classes('bg-green-600 text-white font-bold h-8 text-xs')
                                                            ui.button( 'Reject', on_click=lambda  id=p['id'],inp=amount_input: update_payment_status(id,'Rejected',inp.value)).classes('bg-red-600 text-white font-bold h-8 text-xs')
                                            

                        # --- ⚡ DETAIL VIEW: ELECTRIC & GAS INVOICE GENERATOR ---
                        elif state.room_sub_tab in ["electric", "gas"]:
                            state.bill_type = "Electric" if state.room_sub_tab == "electric" else "Gas"
                            
                            with ui.card().classes('p-4 w-full max-w-4xl shadow-md mx-auto mt-2 bg-white'):
                                ui.label(f'{state.bill_type} Ledger').classes('text-xl text-green-800 font-bold mb-1 text-center w-full')
                                
                                # Tab Navigation
                                # --- TAB NAVIGATION SECTION (FIXED FOR 3 TABS) ---
                                with ui.row().classes('w-full p-1 bg-gray-100 rounded-lg shadow-inner mb-4 border'):
                                    # Current Tab Button
                                    ui.button('📅 CURRENT', on_click=lambda: (setattr(state, 'billing_tab', 'current'), main_container.refresh())) \
                                        .classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.billing_tab != 'current' else 'unelevated color="green-700" text-color=white')
                                    # History Tab Button
                                    ui.button('📜 HISTORY', on_click=lambda: (setattr(state, 'billing_tab', 'history'), main_container.refresh())) \
                                        .classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.billing_tab != 'history' else 'unelevated color="green-700" text-color=white')
                                    # Requested Tab Button
                                    ui.button('🔔 REQUESTED', on_click=lambda: (setattr(state, 'billing_tab', 'requested'), main_container.refresh())) \
                                        .classes('flex-1 font-bold text-[10px] h-9').props(f'flat' if state.billing_tab != 'requested' else 'unelevated color="amber-800" text-color=white')
                                if state.billing_tab == "current":
                                    c_prev_read, c_prev_date = "0", "N/A"
                                    bill_exists = None
                                    
                                    # Fetch Data
                                    if state.renter_id:
                                        try:
                                            # Last Reading
                                            last = supabase.table('utility_billing_ledger').select('curr_reading, curr_reading_date').eq('renter_id', state.renter_id).eq('bill_type', state.bill_type).order('created_at', desc=True).limit(1).execute()
                                            if last.data:
                                                c_prev_read = str(last.data[0]['curr_reading'])
                                                c_prev_date = last.data[0]['curr_reading_date']
                                            else:
                                                print("DEBUG: No last record found for this renter.")
                                            # Current Record
                                            curr = supabase.table('utility_billing_ledger').select('*').eq('renter_id', state.renter_id).eq('bill_type', state.bill_type).eq('bill_month', state.selected_month).eq('bill_year', datetime.now().year).single().execute()
                                            bill_exists = curr.data
                                        except: pass

                                    # UI State: Edit Mode ya Read Only
                                    edit_mode = getattr(state, 'edit_mode', False)

                                    if bill_exists and not edit_mode:
                                        with ui.row().classes('w-full items-start'):
                                        # READ-ONLY VIEW
                                            with ui.column().classes('w-2/3 gap-1'):
                                                ui.label('✅ Bill Details').classes('font-bold text-green-800')
                                                ui.label(f"Pre. Reading: {bill_exists.get('prev_reading')} kWh").classes('text-sm')
                                                ui.label(f"Cur. Reading: {bill_exists.get('curr_reading')} kWh").classes('text-sm')
                                                ui.label(f"Extra unit : {bill_exists.get('extra_units', 0)}").classes('text-sm')
                                                ui.label(f"Rate: ₹{bill_exists.get('rate_per_unit')}").classes('text-sm')
                                                ui.label(f"Total Consumed: {bill_exists.get('total_consumed_units', 0)} Units").classes('text-sm font-bold text-blue-800')
                                                ui.label(f"Total Amount: ₹ {bill_exists.get('total_amount', 0)}").classes('text-lg font-black text-green-900')

                                            with ui.column().classes('w-1/3 items-end'):
                                                img_url = bill_exists.get('bill_img_url')
                                                if img_url:
                                                    ui.image(img_url).classes('w-20 h-20 rounded border shadow-sm')
                                                else:
                                                    ui.label("No Image").classes('text-[10px] text-gray-400')
                                        # READ-ONLY VIEW KE ANDAR
                                        with ui.row().classes('w-full gap-2 mt-4'):
                                            ui.button('EDIT BILL', on_click=lambda: (setattr(state, 'edit_mode', True), main_container.refresh())) \
                                                .classes('flex-1 bg-orange-600 text-white font-bold')
                                                
                                            ui.button('📤 Share WA', on_click=lambda: share_bill_on_whatsapp(bill_exists, state.renter_id)) \
                                                .classes('flex-1 bg-green-600 text-white font-bold')                      
                                    else:
                                        # FORM VIEW (EDITABLE)
                                        
                                        show_prev_read = bill_exists.get('prev_reading', '0') if (edit_mode and bill_exists) else c_prev_read
                                        show_prev_date = bill_exists.get('prev_reading_date', 'N/A') if (edit_mode and bill_exists) else c_prev_date

                                        ui.label(f"Previous Reading: {show_prev_read}").classes('font-bold text-gray-700')
                                        ui.label(f"Date: {show_prev_date}").classes('text-[10px] text-blue-600 mb-2')

                                        kwh_input = ui.input('Current Reading', value=bill_exists.get('curr_reading', '') if bill_exists else '').props('outlined dense type="number"')
                                        rate_input = ui.input('Rate per unit', value=bill_exists.get('rate_per_unit', '9.0')if bill_exists else '9.0').props('outlined dense type="number"')
                                        extra_input = ui.input('Extra Units', value=bill_exists.get('extra_units', '0') if bill_exists else '0').props('outlined dense type=number')
                                        def save_bill():
                                            try:
                                                curr_val = float(kwh_input.value or 0)
                                                rate_val = float(rate_input.value or 9.0)
                                                actual_prev = bill_exists.get('prev_reading', float(c_prev_read)) if bill_exists else float(c_prev_read)
                                                actual_prev_date = bill_exists.get('prev_reading_date', c_prev_date) if bill_exists else c_prev_date

                                               
                                                current_head = state.active_renter_head_id
                                                if not current_head:
                                                    # Emergency fetch agar state mein nahi hai
                                                    res = supabase.table('renters').select('head_member_id').eq('id', state.renter_id).single().execute()
                                                    if res.data:
                                                        current_head = res.data.get('head_member_id')

                                                payload = {
                                                    "renter_id": state.renter_id, "bill_type": state.bill_type,
                                                    "bill_month": state.selected_month, "bill_year": datetime.now().year,
                                                    "prev_reading": float(actual_prev), "curr_reading": curr_val,
                                                    "rate_per_unit": rate_val,
                                                    "extra_units": int(extra_input.value or 0),
                                                    "status": "Submitted",
                                                    "head_id": current_head,
                                                    "room_no": state.selected_room,
                                                    "prev_reading_date": actual_prev_date,
                                                    "curr_reading_date": datetime.now().strftime('%Y-%m-%d')
                                                }
                                                if bill_exists:
                                                    supabase.table('utility_billing_ledger').update(payload).eq('id', bill_exists['id']).execute()
                                                else:
                                                    supabase.table('utility_billing_ledger').insert(payload).execute()
                                                setattr(state, 'edit_mode', False)
                                                ui.notify("Saved!", type="positive")
                                                main_container.refresh()
                                            except Exception as e: ui.notify(str(e), type="negative")

                                        with ui.row().classes('w-full mt-4 gap-2'):
                                            # SAVE BUTTON
                                            ui.button('SAVE', on_click=save_bill).classes('flex-grow bg-green-700 text-white font-bold h-10')
                                            # BACK/CANCEL BUTTON: Edit mode se bahar nikalne ke liye
                                            if bill_exists:
                                                ui.button('BACK', on_click=lambda: (setattr(state, 'edit_mode', False), main_container.refresh())).classes('flex-grow bg-gray-400 text-white font-bold h-10')                           
                                elif state.billing_tab == "history":
                                    # 1. Database se options fetch karo
                                    options = []
                                    try:
                                        res = supabase.table('utility_billing_ledger') \
                                            .select('bill_month, bill_year') \
                                            .eq('renter_id', state.renter_id) \
                                            .eq('bill_type', state.bill_type) \
                                            .execute()
                                        
                                        if res.data:
                                            raw_list = [f"{r['bill_month']} {r['bill_year']}" for r in res.data]
                                            options = sorted(list(set(raw_list)), reverse=True)
                                    except: pass

                                    # 2. Dropdown UI aur Safety Check
                                    # Yahan hum 'selected_hist' define kar rahe hain jo neeche kaam aayega
                                    current_options = options if options else ["N/A"]
                                    if state.history_month not in current_options:
                                        state.history_month = current_options[0]
                                    
                                    selected_hist = state.history_month  # Yahan variable define hua!
                                    
                                    ui.select(
                                        options=current_options, 
                                        value=selected_hist, 
                                        label="Select Month/Year", 
                                        on_change=lambda e: (setattr(state, 'history_month', e.value), main_container.refresh())
                                    ).props('outlined dense').classes('w-full mb-4')

                                    # 3. Data Query Logic
                                    hist_data = None
                                    if options and selected_hist != "N/A":
                                        try:
                                            parts = selected_hist.split()
                                            q_month, q_year = parts[0], int(parts[1])
                                            resp = supabase.table('utility_billing_ledger') \
                                                .select('*') \
                                                .eq('renter_id', state.renter_id) \
                                                .eq('bill_type', state.bill_type) \
                                                .eq('bill_month', q_month) \
                                                .eq('bill_year', q_year).execute()
                                            if resp.data: hist_data = resp.data[0]
                                        except Exception as e:
                                            print("Data Query Error:", e)

                                    # 4. Display UI
                                    with ui.card().classes('w-full p-4 bg-white border rounded-lg shadow-sm'):
                                        ui.label(f"{state.history_month} Record").classes('text-green-800 font-bold mb-2 underline')
                                        with ui.row().classes('w-full items-start'):
                                            with ui.column().classes('w-2/3'):
                                                ui.label(f"Prev Reading: {hist_data.get('prev_reading', 'N/A') if hist_data else 'N/A'} kWh").classes('font-bold')
                                                ui.label(f"{hist_data.get('prev_reading_date', 'N/A') if hist_data else 'N/A'}").classes('text-[10px] text-blue-600 mb-0')
                                                ui.label(f"Curr Reading: {hist_data.get('curr_reading', 'N/A') if hist_data else 'N/A'} kWh").classes('font-bold')
                                                ui.label(f"{hist_data.get('curr_reading_date', 'N/A') if hist_data else 'N/A'}").classes('text-[10px] text-blue-600 mb-1')
                                                ui.separator().classes('my-1')
                                                ui.label(f"Rate: ₹ {hist_data.get('rate_per_unit', 'N/A') if hist_data else 'N/A'}")
                                                ui.label(f"Extra Units: {hist_data.get('extra_units', 'N/A') if hist_data else 'N/A'}")
                                                ui.label(f"Total Consumed: {hist_data.get('total_consumed_units', 'N/A') if hist_data else 'N/A'} Units").classes('font-bold text-blue-800')
                                                ui.label(f"Total Amount: ₹ {hist_data.get('total_amount', 'N/A') if hist_data else 'N/A'}").classes('text-lg font-black text-green-800')

                                            # Right: Image Preview
                                            with ui.column().classes('w-1/3 items-end'):
                                                img_url = hist_data.get('bill_img_url') if hist_data else None
                                                if img_url:
                                                    ui.image(img_url).classes('w-20 h-20 rounded border shadow-sm')
                                                else:
                                                    ui.label("No Image").classes('text-[10px] text-gray-400')
                                elif state.billing_tab == "requested":
                                    # Fetching logic: Jo 'SUBMITTED' hai wo uthao
                                    req_data = None
                                    try:
                                        resp = supabase.table('utility_billing_ledger') \
                                            .select('*') \
                                            .eq('renter_id', state.renter_id) \
                                            .ilike('status_image', 'SUBMITTED%') \
                                            .execute()
                                        if resp.data: req_data = resp.data[0]
                                    except: pass

                                    if req_data:
                                        raw_val = req_data.get('status_image', 'SUBMITTED|0|N/A')
                                        parts = raw_val.split('|')
                                        reading_val = parts[1] if len(parts) > 1 else '0'
                                        
                                        ui.label("🔔 Renter Submission Pending").classes('text-amber-800 font-bold mb-2')
                                        
                                        # Reading input (Owner yahan edit karega)
                                        reading_input = ui.input('Final Reading', value=reading_val).props('outlined dense type=number')
                                        ui.label(f"Submitted Date: {parts[2] if len(parts) > 2 else 'N/A'}").classes('text-[10px] text-gray-500 mb-4')

                                        # Image Preview (Same logic as current/history)
                                        if req_data.get('bill_img_url'):
                                            ui.image(req_data.get('bill_img_url')).classes('w-24 h-24 rounded border mb-4')
                                        else:
                                            ui.label("No Image Attached").classes('text-xs text-gray-400 mb-4')

                                        # Action Buttons
                                        with ui.row().classes('w-full gap-2'):
                                            ui.button('APPROVE', on_click=lambda: update_status(req_data['id'], reading_input.value, 'APPROVED')).classes('bg-green-600 flex-grow')
                                            ui.button('REJECT', on_click=lambda: update_status(req_data['id'], '0', 'REJECTED')).classes('bg-red-600 flex-grow')
                                    else:
                                        ui.label("No pending submissions").classes('text-center w-full mt-10 text-gray-500')

                                    def update_status(row_id, final_reading, status):
                                        # New format: "STATUS|READING|DATE"
                                        new_val = f"{status}|{final_reading}|{datetime.now().strftime('%Y-%m-%d')}"
                                        supabase.table('utility_billing_ledger').update({'status_image': new_val}).eq('id', row_id).execute()
                                        main_container.refresh()
                        # --- ⚙️ TAB 5: SETTINGS SYSTEM MANAGEMENT ---
                        # --- ⚙️ TAB 5: SETTINGS SYSTEM MANAGEMENT ---
                        elif state.room_sub_tab == "settings":
                            with ui.card().classes('p-4 w-full max-w-4xl shadow-md mx-auto mt-2 bg-white gap-3'):
                                with ui.column().classes('w-full bg-slate-50 border p-3 rounded-xl gap-1 items-center justify-center text-center'):
                                    # --- STATUS TOGGLE ENGINE ---
                                    def toggle_renter_status():
                                        new_status = "LEFT" if renter_status_val == "ACTIVE" else "ACTIVE"
                                        try:
                                            supabase.table('renters').update({"status": new_status}).eq('id', state.renter_id).execute()
                                            ui.notify(f"Status changed to {new_status}", type='positive')
                                            main_container.refresh()
                                        except Exception as e:
                                            ui.notify(f"Update failed: {e}", type='negative')

                                    ui.label('Renter Status').classes('text-[10px] font-bold text-slate-400 uppercase')
                                    ui.button(renter_status_val, on_click=toggle_renter_status).props(
                                        f'color={"green-700" if renter_status_val == "ACTIVE" else "red-600"}'
                                    ).classes('font-black text-lg w-full')
                                    
                                    with ui.column().classes('gap-0 text-slate-400 text-xs font-normal mt-1'):
                                        ui.label(f"Booking Date: {booking_date_string}")
                                        if renter_status_val == "LEFT":
                                            ui.label(f"Left Date: {datetime.now().strftime('%d-%b-%Y')}")
                                
                                ui.separator().classes('my-1')
                                ui.label('History Logs Controls').classes('text-xs font-bold text-slate-500 uppercase tracking-wider')
                                
                                with ui.expansion('Electric History Configuration', icon='bolt').classes('w-full border rounded-lg bg-gray-50'):
                                    with ui.row().classes('w-full p-3 items-center justify-between bg-white rounded-b-lg'):
                                        ui.switch('Show History Data Tab', value=state.electric_history_enabled, on_change=lambda e: setattr(state, 'electric_history_enabled', e.value)).props('dense color=green').classes('text-sm font-medium')
                                
                                with ui.expansion('Gas History Configuration', icon='local_fire_department').classes('w-full border rounded-lg bg-gray-50 mt-1'):
                                    with ui.row().classes('w-full p-3 items-center justify-between bg-white rounded-b-lg'):
                                        ui.switch('Show History Data Tab', value=state.gas_history_enabled, on_change=lambda e: setattr(state, 'gas_history_enabled', e.value)).props('dense color=green').classes('text-sm font-medium')
                # 🎓 SCREEN 5: EDUCATION PORTAL
                elif state.current_screen == "education_view":
                    ui.label("Education Portal").classes('text-base font-black text-slate-800 w-full')
                    with ui.card().classes('w-full p-4 bg-white border rounded-2xl text-center'):
                        ui.icon('picture_as_pdf', size='3rem').classes('text-green-700')
                        ui.label('PDF storage & study cabinet dashboard area.').classes('text-xs text-slate-400 mt-1')

                # 🛠️ DEVELOPER MANAGEMENT SCREEN
                elif state.current_screen == "manage_admins" and state.user_role == 'developer':
                    ui.label('Developer Administration Panel').classes('text-base font-black text-slate-800 border-b pb-1 w-full')
                    
                    with ui.card().classes('w-full p-3 border rounded-xl bg-white shadow-none'):
                        ui.label('Add New Admin Account').classes('text-xs font-bold text-green-800')
                        adm_email = ui.input('Enter Admin Email').props('outlined dense').classes('w-full')
                        
                        def trigger_add_admin():
                            if not adm_email.value or '@' not in str(adm_email.value):
                                ui.notify('Sahi email daalein', type='warning')
                                return
                            try:
                                supabase.table('hub_users').insert({"email": str(adm_email.value).strip().lower(), "role": "admin", "status": "ACTIVE"}).execute()
                                ui.notify('Naya Admin register ho gaya!', type='positive')
                                adm_email.value = ""
                                main_container.refresh()
                            except Exception as ex:
                                ui.notify(f"Error: {ex}", type='negative')
                                
                        ui.button('Register Admin', on_click=trigger_add_admin).classes('bg-green-700 text-white text-xs w-full h-8 mt-1')

                    ui.label('Registered Admins Master Registry').classes('text-xs font-bold text-slate-500 mt-2')
                    try:
                        admins_res = supabase.table('hub_users').select('*').eq('role', 'admin').execute()
                        state.all_admins_list = admins_res.data if admins_res.data else []
                    except: pass
                        
                    with ui.column().classes('w-full gap-2 mt-1'):
                        for adm in state.all_admins_list:
                            with ui.card().classes('w-full p-2 bg-white border rounded-xl shadow-none'):
                                with ui.row().classes('w-full justify-between items-center no-wrap'):
                                    with ui.column().classes('gap-0 max-w-[160px]'):
                                        ui.label(adm['email']).classes('text-xs font-bold text-slate-800 truncate')
                                        ui.label(f"Status: {adm['status']}").classes(f"text-[10px] font-bold " + ("text-emerald-600" if adm['status'] == "ACTIVE" else "text-rose-600"))
                                    
                                    with ui.row().classes('gap-1'):
                                        if adm['status'] == 'ACTIVE':
                                            ui.button('Pause', on_click=lambda email=adm['email']: (supabase.table('hub_users').update({"status": "PAUSED"}).eq('email', email).execute(), main_container.refresh())).classes('bg-orange-500 text-white text-[9px] px-2 h-6 rounded')
                                        else:
                                            ui.button('Active', on_click=lambda email=adm['email']: (supabase.table('hub_users').update({"status": "ACTIVE"}).eq('email', email).execute(), main_container.refresh())).classes('bg-green-600 text-white text-[9px] px-2 h-6 rounded')
                                        ui.button('Delete', on_click=lambda email=adm['email']: (supabase.table('hub_users').delete().eq('email', email).execute(), ui.notify('Account Deleted'), main_container.refresh())).classes('bg-red-600 text-white text-[9px] px-2 h-6 rounded')

            main_container()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Morya Mobile Hub', port=8080, host='0.0.0.0', storage_secret='morya_master_999')