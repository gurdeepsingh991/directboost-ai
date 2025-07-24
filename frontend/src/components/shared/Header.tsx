
export default function Header() {
    return (
        <div className="bg-blue-500 w-full h-14 shadow-xl flex items-center justify-between gap-6 px-6 text-white font-medium fixed">
            <a href="/"> DIRECT BOOST AI</a>
            <div className="space-x-7">
                <a href="/about" className="hover:underline">About Us</a>
                <a href="/contact" className="hover:underline">Contact Us</a>
                <a href="/help" className="hover:underline">Help</a>
                <a href="/login" className="hover:underline">Login</a>
            </div>

        </div>


    )
}
