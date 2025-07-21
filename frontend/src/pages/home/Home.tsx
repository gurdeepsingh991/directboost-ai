import Button from "../../components/shared/Button";

export default function Home() {
  const getStarted = () => {
  }
  return (
    <>
      <div className='flex flex-col items-center pt-30'>
        <h1 className="text-3xl">Welcome to Direct Boost AI</h1>
        <p className="text-xl">An AI solution to boost direct bookings for your hotel by genrating pesonalised eamail promotions.</p>
        <div className="mt-5">
          <Button type="normal" label="Get Started" onClick={getStarted} />
        </div>
      </div>
    </>
  )
}
